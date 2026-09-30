# Wagtail Marketing Starter Kit

A modern, flexible foundation for building high-performance marketing websites with Wagtail CMS.

## Features

- **Django 5.2 LTS** and **Wagtail 7.4 LTS** - Latest stable versions
- **SQLite** as primary database with Litestream replication
- **Tailwind CSS v4** with **DaisyUI v5** - Modern utility-first CSS framework
- **htmx 4** + **Stimulus 3** - Enhanced interactivity without complex JavaScript
- **StreamField Blocks** - Flexible content composition system
- **Navigation Snippets** - Reusable menu system
- **SEO Ready** - Built-in SEO functionality with wagtail-seo
- **Caching** - Performance optimization with wagtail-cache
- **Forms** - Flexible form handling with wagtail-flexible-forms
- **Django-Vite Integration** - Modern asset pipeline

## Project Structure

```
├── apps/
│   ├── blocks/                     # Custom StreamField blocks
│   ├── core/                       # Base models, utilities and the sample-data command
│   ├── pages/                      # Page models and templates
│   ├── navigation/                 # Navigation menu snippets
│   ├── search/                     # Site search functionality
│   ├── settings/                   # Site settings
│   ├── snippets/                   # Content snippets
│   └── forms/                      # Form handling
├── config/                         # Django settings and configuration
├── db/                             # SQLite database files
├── frontend/                       # Frontend source files and build configuration
│   ├── src/                        # Source files
│   │   ├── app/                    # JavaScript application code
│   │   │   ├── main.js             # Main JavaScript entry point
│   │   │   └── controllers/        # Stimulus controllers
│   │   │       └── navbar.js
│   │   └── css/                    # CSS source files
│   │       └── styles.css
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.mjs             # Vite build configuration
│   └── pnpm-lock.yaml              # pnpm lock file
├── prod/                           # Production configuration
│   └── freebsd/                    # nginx, litestream, pf, rc.d, deploy scripts
├── scripts/                        # Optional checks that need a real browser
├── templates/                      # Django templates
│   ├── pages/                      # Page-specific templates
│   ├── blocks/                     # StreamField block templates
│   ├── includes/                   # Reusable template components
│   └── snippets/                   # Snippet templates
├── .env                            # Environment variables
├── .gitignore
├── justfile                        # Canonical entrypoint (dev and FreeBSD prod)
├── manage.py
├── mise.development.toml           # mise tools for dev
├── mise.production.toml            # mise tools for prod
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## Development Setup

Requires Linux or macOS. [mise](https://mise.jdx.dev/) provides Python, uv, Node and pnpm; `just` runs the recipes.

1. **Install mise and just**

   ```bash
   # macOS
   brew install mise just
   ```

2. **Install dependencies**

   ```bash
   mise trust && mise install
   just install
   ```

3. **Start the development environment**

   ```bash
   just dev
   ```

4. **Access the application**

   - Django: http://localhost:8000
   - Wagtail Admin: http://localhost:8000/admin/
   - Django Admin: http://localhost:8000/django-admin/
   - Vite Dev Server: http://localhost:5173

The database is a SQLite file at `db/database.db`; media files live on disk.

## Development Workflow

`just` is the only entrypoint. Run `just` to list all recipes.

- `just dev` - Run Django (uvicorn) and Vite together
- `just django-dev` / `just vite-dev` - Run one of them alone
- `just dev-migrate` - Apply database migrations
- `just makemigrations` - Create new migrations
- `just seed` - Build the sample site in the development database
- `just unseed` - Remove the sample site again
- `just vite-build` - Build frontend assets (commit the result, the server never runs pnpm)
- `just lint` - Check formatting and unused imports
- `just test` - Run the test suite
- `just install` - Sync Python and frontend dependencies and install the pre-commit hooks
- `uv run manage.py createsuperuser` - Create an admin user

### Sample data

`just seed` (`manage.py seed_demo`) builds a site you can click through: a home
page using every block type, a flex page, a showcase with sections, items and
links, project / service / portfolio pages, a contact form, both menus and the
site settings. It is idempotent, so run it again after a `git pull`. It replaces
Wagtail's placeholder home page, but only while that page has no children.

`just unseed` (`manage.py seed_demo --clear`) takes it all back out: the sample
pages, snippets, tags, image, menu items and site settings, leaving an empty
site that still serves. It only touches the sample content, so admin users and
anything else you added survive.

The test suite builds the same content, so the sample site is exercised on
every run (`tests/test_sample_site.py`).

### Tests

`just test` runs the suite (pytest + pytest-django). Nothing else is needed to
set up: pytest builds and destroys its own database, so the development
database at `db/database.db` is never touched, and no `.env` file is required
(development defaults live in `config/settings/base.py`).

To run one file or one test:

```sh
uv run pytest tests/test_showcase.py
uv run pytest tests/test_search.py -k pagination
```

Every test that touches the database is marked `django_db` and runs against a
throwaway SQLite database. `tests/conftest.py` points static and media files at
temporary directories (so a run leaves nothing behind), and the `seeded_home`
fixture builds the sample site by calling the same `seed_demo` command you run
by hand, so the tests exercise the real command instead of hand-made fixtures.
`tests/test_sample_site.py` then walks the page tree and requests every page.

What the suite covers: every template compiles; models match the migrations;
the sample site is crawled page by page and every block, menu and showcase item
renders; the contact form validates, stores and emails a submission; search
finds seeded pages; entity pages are served at their slug; menu edits are
visible immediately; the frontend interactivity stack is htmx 4 throughout;
production settings refuse insecure configuration; `requirements.txt` matches
`uv.lock`; and the Litestream configuration stays durable.

The one thing a pytest run cannot prove is that the JavaScript actually drives
the browser. `scripts/check_frontend.py` checks that in a real browser (htmx
boosted navigation, AJAX form posts, Stimulus reconnecting after a swap). With
`just django-dev` and `just seed` already done:

```sh
uv run --with playwright playwright install chromium
uv run --with playwright python scripts/check_frontend.py
```

Run `just lint` and `just test` before committing (the pre-commit hook also
runs ruff automatically).

### Testing production locally

`just local-prod-check` runs the production configuration on this machine against
throwaway paths: it collects static files from the committed build (django-vite
reads the manifest from `STATIC_ROOT`, so this runs first, as it does on the
server), runs Django's deployment checks with warnings treated as failures,
applies every migration to an empty database, and checks that none is missing.

`just local-prod-smoke` serves the same configuration on
<http://127.0.0.1:8001> with sample content, so you can click through the built
assets instead of the dev server: no HMR, no `dev.js`, WhiteNoise serving static
files, media from disk, `DEBUG` off. The browser check takes any origin:

```sh
just local-prod-smoke   # leave it running
CHECK_BASE_URL=http://127.0.0.1:8001 uv run --with playwright python scripts/check_frontend.py
```

Both recipes use `config/settings/local_prod.py`: the production settings with the
server-only pieces relaxed (no TLS redirect or secure cookies, media on disk,
database under `/tmp`). The deployment never uses it.

### Cleaning up

`just unseed` removes the sample content but keeps the site, its users and your
own pages. To go further back, delete the development database and migrate
again: `rm db/database.db && just dev-migrate` (this drops admin users and
everything else in it).

`just clean` removes `.venv`, `frontend/node_modules` and `frontend/dist`. The
`frontend/dist` build is committed, so restore it with
`git checkout frontend/dist` or rebuild it with `just vite-build`.

The browser check downloads Chromium into `~/.cache/ms-playwright`; delete that
directory if you no longer want it.

### Known console noise

With the Dark Reader extension enabled, the dev server logs
`Uncaught HierarchyRequestError: Failed to execute 'insertRule' on
'CSSStyleRule'` from the extension's own `index.js` whenever Vite re-injects the
stylesheet. Dark Reader rebuilds the page's CSS rule by rule, Tailwind v4 emits
nested rules, and Chromium refuses to nest a rule inside one of those. The page
itself is unaffected (a clean browser logs nothing), so ignore it or disable the
extension for `localhost`.


## Production

`prod/freebsd/` holds the nginx, Litestream, pf and rc.d configuration plus the
deploy scripts. Follow `prod/freebsd/README.md`; its environment section lists
every setting production requires and how to install them
(`.env.prod.example` → `.env.prod` → `just setup-env`).

## Content Modeling

### BasePage Model

Abstract base page model that defines common fields and functionality that should be shared across all page types.
Inherits from `SeoMixin` and `Page` to provide SEO functionality via wagtail-seo.

- SEO Title and Description
- Open Graph Image
- Structured data support
- UUID field for stable identifiers

### FlexPage Model

A flexible page model that can be used for the homepage or other standard pages.
It uses a StreamField for maximum content flexibility.
Inherits from `BasePage`.

### BaseEntityPage Model

Abstract base page for all showcase entities with common fields.
Inherits from `FlexPage` (and thus `BasePage`).

- Tag (ForeignKey to Tag snippet)
- URL type preference (SEO-friendly or UUID-based)

### Showcase Pages

Specialized pages for displaying collections of entities:

- ProjectShowcasePage: Displays projects
- ServiceShowcasePage: Displays services
- PortfolioShowcasePage: Displays portfolio items
- ResourceShowcasePage: Displays resources

### ProjectPage, ServicePage, PortfolioItemPage Models

Specific page types for different entity categories:

- ProjectPage: Inherits from `BaseEntityPage`
- ServicePage: Inherits from `BaseEntityPage`
- PortfolioItemPage: Inherits from `BaseEntityPage`

### StreamField Blocks

The starter kit includes a comprehensive set of reusable blocks:

**Basic Blocks:**

- RichTextBlock
- HeadingBlock
- ImageBlock (with alt text and caption)
- EmbedBlock
- QuoteBlock

**Component Blocks:**

- HeroBlock: Primary page headers with headings, text, background images, and CTAs
- CardBlock: Repeatable block with image, title, text, and link
- CallToActionBlock: Visually distinct block to encourage user action
- ButtonBlock: Configurable button with text, link, and style choices

**Layout Blocks:**

- TwoColumnBlock: Structural block for two-column layouts
- ThreeColumnBlock: Structural block for three-column layouts

### Navigation Snippets

- Menu: Container for hierarchical menu items
- MenuItem: Individual menu items with links to pages or URLs, supporting nested structures

### Content Snippets

- Tag: For categorizing and organizing showcase entities

## Frontend Architecture

### CSS Framework

- Tailwind CSS v4 with DaisyUI v5
- Utility-first approach for rapid development
- Responsive design built-in

### JavaScript

- htmx 4 (boosted navigation, AJAX forms) & Stimulus 3 for dynamic interactions and complex behaviors when needed

### Asset Pipeline

- Vite for bundling and optimization
- pnpm for JavaScript package management
- Development and production build configurations

## Performance Features

- SQLite as primary database with Litestream replication
- Local-memory caching with wagtail-cache
- Frontend cache invalidation
- Template fragment caching
- Image optimization with Wagtail's image tag
- Asset minification for production

## Development Tools

- Pre-commit hooks for code quality
- Type hints throughout the codebase
- Automated testing framework

## Deployment

Production runs on FreeBSD, provisioned end to end by the `prod-*` and `freebsd-*` recipes in the `justfile` (nginx, litestream, pf, rc.d services).

- Environment variables for configuration (`.env.prod` -> `/usr/local/etc/wagtail/env`)
- WhiteNoise for static file serving
- Litestream for SQLite replication to S3
- `prod/freebsd/scripts/deploy.sh` for pull-based deploys

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
