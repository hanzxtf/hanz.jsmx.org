"""Check the frontend stack in a real browser.

The pytest suite covers the server-rendered site; this script covers what only
a browser can prove: htmx boosted navigation, AJAX form posts, and Stimulus
controllers reconnecting after a swap.

Needs a development server with sample content in another terminal:

    just django-dev
    just seed

Then (the first run downloads Chromium, ~115MB):

    uv run --with playwright playwright install chromium
    uv run --with playwright python scripts/check_frontend.py

Exits non-zero if any check fails.
"""

import re
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - depends on how the script is run
    sys.exit(
        "Playwright missing. Run: uv run --with playwright python scripts/check_frontend.py"
    )

BASE = "http://127.0.0.1:8000"
failures = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}{f' -> {detail}' if detail else ''}")
    if not condition:
        failures.append(label)


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 900})

        console = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text}"))
        page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))

        boosted = []

        def note_boost(request):
            headers = {key.lower(): value for key, value in request.headers.items()}
            if headers.get("hx-boosted") == "true":
                boosted.append(f"{request.method} {request.url}")

        page.on("request", note_boost)

        response = page.goto(f"{BASE}/search/")
        if response is None or response.status >= 400:
            sys.exit(f"Cannot reach {BASE}. Start `just django-dev` first.")

        # the vite dev server reloads the page the first time it optimises a dependency
        page.wait_for_timeout(700)

        # the library is loaded and the site opts into boost
        check("htmx is on window", page.evaluate("typeof window.htmx") == "object")
        check(
            "htmx major version is 4",
            str(page.evaluate("window.htmx.version")).startswith("4"),
            page.evaluate("window.htmx.version"),
        )
        check(
            "the body boosts links and forms",
            page.evaluate("document.body.getAttribute('hx-boost:inherited')") == "true",
        )

        modules_before = page.evaluate(
            "document.querySelectorAll('script[type=module]').length"
        )
        home_html = page.request.get(f"{BASE}/").text()
        home_description = re.search(
            r'<meta name="description" content="([^"]*)"', home_html
        ).group(1)

        # boosted link navigation
        page.evaluate("window.__probe = 'kept'")
        page.click('header a[href="/"]')
        page.wait_for_url(f"{BASE}/")
        page.wait_for_timeout(500)

        check(
            "link navigation is AJAX (no reload)",
            page.evaluate("window.__probe") == "kept",
        )
        check("history URL was pushed", page.url == f"{BASE}/", page.url)
        check("HX-Boosted request header was sent", len(boosted) >= 1, boosted[:1])

        expected_title = re.search(r"<title>(.*?)</title>", home_html).group(1)
        check(
            "the page title came from the response",
            page.title() == expected_title,
            f"{page.title()} (server says {expected_title})",
        )
        check(
            "the head merge added the new meta description",
            page.evaluate("document.querySelector('meta[name=description]')?.content")
            == home_description,
            page.evaluate("document.querySelector('meta[name=description]')?.content"),
        )
        check(
            "the head merge did not duplicate the bundle",
            page.evaluate("document.querySelectorAll('script[type=module]').length")
            == modules_before,
            page.evaluate("document.querySelectorAll('script[type=module]').length"),
        )

        # Stimulus reconnects on the swapped body: open the mobile menu
        page.click('[data-action="navbar#toggleMenu"]')
        page.wait_for_timeout(400)
        menu = page.evaluate(
            """() => {
                const menu = document.querySelector('[data-navbar-target="mobileMenu"]');
                return {hidden: menu.classList.contains('hidden'),
                        visibility: getComputedStyle(menu).visibility};
            }"""
        )
        check(
            "Stimulus reconnected after the swap",
            menu["hidden"] is False and menu["visibility"] != "hidden",
            menu,
        )

        # boosted GET form
        page.goto(f"{BASE}/search/")
        page.evaluate("window.__probe = 'search'")
        page.fill('input[name="query"]', "Blue")
        page.press('input[name="query"]', "Enter")
        page.wait_for_url("**/search/?query=Blue")
        page.wait_for_timeout(500)

        check(
            "search form submitted over AJAX",
            page.evaluate("window.__probe") == "search",
        )
        check(
            "search results rendered",
            'Search results for "Blue"' in page.inner_text("body"),
        )
        check("search term is in the URL", "query=Blue" in page.url, page.url)

        # boosted POST form, including the CSRF token
        page.goto(f"{BASE}/contact/")
        page.evaluate("window.__probe = 'contact'")
        page.fill('input[name="name"]', "Ada Lovelace")
        page.fill('input[name="email"]', "ada@example.com")
        page.fill('textarea[name="message"]', "Hello from a real browser.")
        page.click('form[action="/contact/"] button[type="submit"]')
        page.wait_for_timeout(1500)

        check(
            "contact form posted over AJAX",
            page.evaluate("window.__probe") == "contact",
        )
        check(
            "contact form showed its landing page",
            "Thanks, your message is on its way." in page.inner_text("body"),
        )
        check(
            "contact form stayed on its URL", page.url == f"{BASE}/contact/", page.url
        )
        check(
            "the contact POST was boosted",
            any("POST" in entry and "/contact/" in entry for entry in boosted),
            boosted[-1:],
        )

        # a link in the mobile menu, which closes the menu as it navigates
        page.goto(f"{BASE}/")
        page.evaluate("window.__probe = 'nav'")
        page.click('[data-action="navbar#toggleMenu"]')
        page.wait_for_timeout(400)
        page.click('ul[data-navbar-target="mobileMenu"] a[href="/contact/"]')
        page.wait_for_url(f"{BASE}/contact/")
        page.wait_for_timeout(500)

        check("menu link navigated over AJAX", page.evaluate("window.__probe") == "nav")
        check(
            "menu link rendered the contact page",
            page.query_selector('form[action="/contact/"] input[name="name"]')
            is not None,
        )

        # the head merge replaces stale tags instead of accumulating them
        contact_description = re.search(
            r'<meta name="description" content="([^"]*)"',
            page.request.get(f"{BASE}/contact/").text(),
        ).group(1)
        descriptions = page.evaluate(
            """() => Array.from(document.querySelectorAll('meta[name=description]'))
                     .map((meta) => meta.content)"""
        )
        check(
            "the head merge replaced the previous meta description",
            descriptions == [contact_description],
            descriptions,
        )

        errors = [line for line in console if line.startswith(("error", "pageerror"))]
        check("no JavaScript errors in the console", errors == [], errors[:3])

        browser.close()

    print(f"\n{len(boosted)} boosted requests: {boosted}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
