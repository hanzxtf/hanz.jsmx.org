// Development-only behaviour.
//
// main.js loads this file only when Vite reports a dev build, so none of it
// reaches the production bundle.
//
// The head merge (hx-head) drops head elements that the new response does not
// contain. The dev server injects the stylesheet as a <style> tag that no
// response ever carries, so a boosted navigation would strip the page's styling
// and the page would jump as the content reflows. With the built assets the
// stylesheet is a <link> that every response carries, so the merge keeps it:
// tests/test_sample_site.py pins that every page ships the same assets.
document.addEventListener("htmx:head:before:remove", (event) => {
  if (event.detail.headElement.tagName === "STYLE") {
    event.preventDefault();
  }
});
