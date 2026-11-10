# ckanext-auscope-core
Shared CKAN extension providing AuScope branding, themes, reusable UI components and common functionality to simplify maintenance and CKAN upgrades across AuScope repositories.

## Status

Shared branding, header, footer and layouts ([Issue #2](https://github.com/AuScope/ckanext-auscope-core/issues/2),
[Issue #3](https://github.com/AuScope/ckanext-auscope-core/issues/3)).
Enabling the plugin applies AuScope colours, typography, focus styles, repository
branding and responsive layouts on top of CKAN's templates and CSS.

Consumers: AuScope Data Repository, Sample Repository, Instrument Registry (PIDINST)
and the RAiD Repository.

## Requirements

- CKAN 2.12.1
- Python 3.10 or newer (the development image uses Python 3.14)
- Docker or Podman with Compose, for the development environment

## Installation

Install into the Python environment of an existing CKAN 2.12.1 instance:

1. Activate the CKAN virtual environment.
2. Install the extension, either from a clone:

   ```bash
   git clone https://github.com/AuScope/ckanext-auscope-core.git
   cd ckanext-auscope-core
   pip install -e .
   ```

   or directly from GitHub:

   ```bash
   pip install git+https://github.com/AuScope/ckanext-auscope-core.git
   ```

3. Add `auscope_core` to `ckan.plugins` in `ckan.ini`. List it after any
   repository-specific theme plugin, so that plugin can override the shared templates:

   ```ini
   ckan.plugins = my_repository_theme auscope_core ...
   ```

4. Restart CKAN and check that `auscope_core` appears in `extensions` at
   `/api/3/action/status_show`.

## Configuration

The extension adds no configuration options. It changes the defaults of two CKAN
core options:

- `ckan.site_logo`: if it is CKAN's default `/base/images/ckan-logo.png`, it becomes
  `/auscope_core/images/auscope-logo-icon.png`.
- `ckan.favicon`: if it is CKAN's default `/base/images/ckan.ico`, it becomes
  `/auscope_core/images/auscope-favicon.png`.

Any other value is kept, including an empty `ckan.site_logo` (the header then shows
the repository title without a mark), values from `CKAN__SITE_LOGO` /
`CKAN__FAVICON` and values set in the sysadmin config UI. CKAN-generated configs set
the default paths explicitly, so the rule compares values rather than checking
whether the key is set. The repository title is CKAN's native `ckan.site_title`
option; no duplicate AuScope setting is required.

## Theme and branding

Webassets bundles (library `auscope_core`):

| Bundle | Contents | Included by |
|---|---|---|
| `auscope_core/auscope_core-tokens` | `css/tokens.css`: `--auscope-*` design tokens | preloaded by `auscope_core-css` |
| `auscope_core/auscope_core-css` | `css/base.css`, `css/components.css`, `css/branding.css` | `templates/base.html` |
| `auscope_core/auscope_core-js` | placeholder for later shared modules | not included in pages |

Order of the stylesheets in the rendered `<head>`:

1. CKAN `main.css`.
2. `auscope_core-tokens`.
3. `auscope_core-css`.
4. Consumer bundles included after `{{ super() }}` in the consumer's `base.html`
   `styles` block.
5. The `ckan.site_custom_css` inline `<style>`.

List the consumer plugin **before** `auscope_core` in `ckan.plugins`, so the
consumer's `base.html` `{% ckan_extends %}` extends the shared one.

### Customising the theme

- **Override tokens** (preferred). In the consumer's own CSS bundle:

  ```css
  :root {
    --auscope-color-accent: #e87722;
    --auscope-logo-height: 4rem;
  }
  ```

  The full list is in `ckanext/auscope_core/assets/css/tokens.css`. When you change
  a colour that has an `-rgb` companion (for example `--auscope-color-primary` and
  `--auscope-color-primary-rgb`), change both.
- **Sysadmin tweaks**: `ckan.site_custom_css`.
- **Replace or opt out**: in the consumer's `base.html`, override the
  `auscope_core_styles` block. Use
  `{% block auscope_core_styles %}{% asset 'auscope_core/auscope_core-tokens' %}{% endblock %}`
  to keep only the tokens, or leave the block empty to drop the shared styles.
- **Logo and favicon**: set `ckan.site_logo` / `ckan.favicon` (or
  `CKAN__SITE_LOGO` / `CKAN__FAVICON`), for example to
  `/auscope_core/images/auscope-logo-icon.png`. Set `ckan.site_logo =` (empty) to
  show the text title.

Shipped images are served from `/auscope_core/images/`: `auscope-logo.png`,
`auscope-logo-reversed.png` (for dark backgrounds), `auscope-logo-icon.png` and
`auscope-favicon.png`. Licensing and attribution are in
`ckanext/auscope_core/public/auscope_core/ASSETS-LICENSES.md`. The Calibre font is
not shipped (no redistribution licence); the base font is a system font stack.

## Shared templates and layouts

The shared header keeps CKAN's account controls, responsive menu and site search.
It combines `ckan.site_logo` with `ckan.site_title`. The footer supplies common
contact, NCRIS funding, AuScope community and acknowledgement content while keeping
CKAN's language selector. The homepage places the CKAN search across the full
container and leaves the two lower columns available through CKAN's `promoted` and
`featured_organization` blocks. Ordinary pages continue to use CKAN's unmodified
`page.html`, including its skip link, breadcrumb and responsive sidebar.

Consumers list their plugin before `auscope_core` and extend only the block they
need. Repository routes and login/contact workflows stay in the consumer. For
example:

```jinja
{% ckan_extends %}

{% block header_site_navigation_tabs %}
  {{ h.build_nav_main(
    ('dataset.search', _('Records'), ['dataset', 'resource']),
    ('home.about', _('About'))
  ) }}
{% endblock %}
```

Available customisation points are:

- `auscope_header_brand_mark` and `auscope_header_repository_title` in
  `header.html`; the standard CKAN `header_site_navigation_tabs`,
  `header_account_notlogged` and `header_site_search` blocks remain available.
- `auscope_footer_contact`, `auscope_footer_funding`,
  `auscope_footer_community` and `auscope_footer_acknowledgement` in `footer.html`.
- `search`, `promoted` and `featured_organization` in `home/index.html`.
- CKAN's normal `secondary_content`, `primary_content`, `pre_primary`,
  `wrapper_class` and related page blocks for common pages.

For a CKAN-styled content section without copying module markup, import the shared
macro:

```jinja
{% from 'snippets/auscope_core/page_section.html' import page_section %}
{% call page_section(_('Repository guidance')) %}
  <p>Repository-specific content goes here.</p>
{% endcall %}
```

Data, Sample, PIDINST and RAiD should set their own `ckan.site_title`, override the
navigation block with routes supplied by their plugins, and override only footer or
homepage blocks whose content differs. The core intentionally does not provide AAF
routes, contact forms, instrument/platform routes, reporting-year links or
repository-specific homepage copy.

### Visual check

With the development stack running:

1. Set `CKAN__SITE_TITLE=AuScope Data Repository` (or another repository name),
   then open http://localhost:5000/, `/dataset`, `/user/login` and `/about`. Expect a
   light grey masthead with the AuScope icon and title and a teal line under it, a
   full-width white homepage search box above a royal-blue "Popular tags" strip,
   and a three-column grey footer with royal-blue text. The intended look is
   described in [docs/design-baseline.md](docs/design-baseline.md).
2. Press Tab to see focus rings and the skip link. Outlines are royal blue, except
   on "Popular tags" (white on blue); on the search submit button the outline is
   inside the button.
3. On a dataset page, Tab through the Dataset / Groups / Activity tabs and confirm
   the outline is visible.
4. Narrow the window below 992 px and 576 px. At 375 px, Tab to the menu toggler
   (outline visible), open it, and tap a nav link (text stays dark on white).
5. Open a dataset whose notes contain a link and check that the link is underlined.
   To create one, log in as a sysadmin and add a dataset with
   `See [AuScope](https://www.auscope.org.au).` in its description.
6. In DevTools, set a token on `:root` (for example `--auscope-color-primary: #8b0000`
   with `--auscope-color-primary-rgb: 139, 0, 0`) and watch the page update.
7. Set `CKAN__SITE_LOGO` in `.env` and restart `ckan-dev` to see the logo override.

## Development environment

The Compose stack runs `ckan/ckan-dev:2.12.1` with PostgreSQL 15, Redis 7 and two
Solr 9 services (`ckan/ckan-solr:2.12-solr9`). Development and automated tests use
physically separate Solr services and volumes, so test fixtures cannot clear the
development search index. The extension is installed in editable mode and the
repository is bind-mounted into the container, so code changes are live.

```bash
cp .env.example .env            # PowerShell: Copy-Item .env.example .env
docker compose up -d --build    # or: podman compose up -d --build
```

CKAN is served at http://localhost:5000 (port set by `CKAN_PORT_HOST`). The local
sysadmin account is defined by `CKAN_SYSADMIN_*` in `.env`. `.env` holds local
development values only and must never be committed.

If `CKAN_DB_PASSWORD` contains URI-reserved characters, keep its raw value for the
PostgreSQL setup script and percent-encode the password component in
`CKAN_SQLALCHEMY_URL` and `TEST_CKAN_SQLALCHEMY_URL`.

Stop the stack with `docker compose down` (add `-v` to also delete the database,
Solr and file-storage volumes).

## Running tests

With the stack running:

```bash
docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev sh docker/ckan/test-env.sh ckan -c test.ini db init
docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev sh docker/ckan/test-env.sh pytest --ckan-ini=test.ini -v ckanext/auscope_core
```

Always run tests through `docker/ckan/test-env.sh`. The `ckan-dev` container sets
`CKAN_SQLALCHEMY_URL`, `CKAN_SOLR_URL` and `CKAN_REDIS_URL` to the development
services, and CKAN applies these variables over `test.ini`. Without the script,
`clean_db` empties the development database. The script replaces them with the
`TEST_CKAN_*` values from `.env` (`ckan_test`, `solr-test`, Redis database 2) and
refuses to run if a test value is missing or equals the development value. If an
older `.env` sets `TEST_CKAN_SOLR_URL` to the `solr` service, copy the current value
from `.env.example`.

Tests use CKAN core's pytest plugin and fixtures. `test.ini` inherits
`../../src/ckan/test-core.ini`, which resolves inside the `ckan-dev` container. For a
CKAN source install, change the `use = config:` line to point at your CKAN source's
`test-core.ini`, set `solr_url` to a test-only Solr core, and make sure the
`CKAN_*` connection variables are unset or point at test services.

## Linting

```bash
pip install -r dev-requirements.txt
ruff check .
```

## Project structure

```
ckanext-auscope-core/
├── AGENTS.md                    # AI development instructions (canonical rules)
├── docs/                        # architecture.md, decisions.md (ADR log), branding-analysis.md, design-baseline.md
├── .kiro/steering/              # Kiro steering files (point to AGENTS.md and docs/)
├── .github/workflows/test.yml   # CI: tests in ckan/ckan-dev:2.12.1, ruff lint
├── docker-compose.yml           # Development stack: CKAN, PostgreSQL, Solr, Redis
├── docker/
│   ├── ckan/Dockerfile.dev      # ckan-dev image with the extension installed editable
│   ├── ckan/test-env.sh         # Points CKAN at the test DB, Solr and Redis for tests
│   └── postgres/initdb/         # Creates the CKAN role and dev/test databases
├── .env.example                 # Template for the local .env (never commit .env)
├── pyproject.toml               # Package metadata, ckan.plugins entry point, tool config
├── setup.cfg, setup.py          # Setuptools/Babel settings (CKAN cookiecutter layout)
├── requirements.txt             # Runtime dependencies (none beyond CKAN)
├── dev-requirements.txt         # Development tools (ruff)
├── test.ini                     # pytest configuration inheriting CKAN's test-core.ini
└── ckanext/
    └── auscope_core/
        ├── plugin.py            # AuscopeCorePlugin (IConfigurer, logo/favicon defaults)
        ├── templates/
        │   ├── base.html        # Includes the shared CSS
        │   ├── header.html      # Icon/title; preserves CKAN account/nav/search
        │   ├── footer.html      # Shared contact/funding/community content
        │   ├── home/index.html  # Full-width search and reusable lower columns
        │   └── snippets/auscope_core/page_section.html
        ├── public/auscope_core/
        │   ├── images/          # AuScope logos and favicon
        │   └── ASSETS-LICENSES.md
        ├── assets/              # Webassets library "auscope_core"
        │   ├── webassets.yml
        │   ├── css/             # tokens.css, base.css, components.css, branding.css
        │   └── js/              # auscope_core.js (placeholder)
        ├── i18n/                # Translations (empty for now)
        └── tests/               # pytest tests
```

## Documentation

- [AGENTS.md](AGENTS.md): development rules for people and AI agents
- [docs/architecture.md](docs/architecture.md): extension design
- [docs/decisions.md](docs/decisions.md): technical decisions and verification records
- [docs/branding-analysis.md](docs/branding-analysis.md): analysis of the reference
  repositories' branding (Issue #2)
- [docs/design-baseline.md](docs/design-baseline.md): shared visual baseline and
  differences from the legacy sites
