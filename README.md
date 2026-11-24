# ckanext-auscope-core
Shared CKAN extension providing AuScope branding, themes, reusable UI components and common functionality to simplify maintenance and CKAN upgrades across AuScope repositories.

## Status

Shared branding, header, footer and layouts ([Issue #2](https://github.com/AuScope/ckanext-auscope-core/issues/2),
[Issue #3](https://github.com/AuScope/ckanext-auscope-core/issues/3)).
Enabling the plugin applies AuScope colours, typography, focus styles, repository
branding and responsive layouts on top of CKAN's templates and CSS.
Core also exposes dependency-free geographic validation primitives and shared FOR
and EPSG lookup services for consumer extensions; enabling the plugin does not
apply them to any schema automatically.

Consumers: AuScope Data Repository, Sample Repository, Instrument Registry (PIDINST)
and the RAiD Repository.

## Requirements

- CKAN 2.12.1
- Python 3.10 or newer (the development image uses Python 3.14)
- Docker or Podman with Compose, for the development environment

Core has no runtime dependency on other CKAN extensions. Scheming, spatial, DOI,
DCAT, contact, taxonomy, storage, authentication and loaders are optional consumer
capabilities. The current repository inventory, compatibility limitations and
recommended profile-based management are documented in
[docs/extension-compatibility.md](docs/extension-compatibility.md).

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

The extension declares provider URLs, timeouts and result limits under
`ckanext.auscope_core.vocabulary.*`; their defaults and usage are documented in
[Shared FOR and EPSG vocabularies](#shared-for-and-epsg-vocabularies). It also
changes the defaults of two CKAN core options:

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
`ckanext/auscope_core/public/auscope_core/ASSETS-LICENSES.md`.

### Calibre font support

The established repositories use `CalibreWeb-Light.woff` and
`CalibreWeb-Medium.woff`, but neither reference repository documents a licence that
permits redistribution. Core therefore ships no font binaries and no font URLs. Its
tokens use the legacy family names first, followed by maintained system fallbacks:

```css
--auscope-font-family-base: "Calibre-light", Inter, "Segoe UI", Roboto, Arial, sans-serif;
--auscope-font-family-medium: "Calibre-Medium", Inter, "Segoe UI", Roboto, Arial, sans-serif;
```

A consumer with its own permission can serve the WOFF files and declare them in a
consumer bundle loaded after Core:

```css
@font-face {
  font-family: "Calibre-light";
  src: url("/consumer/fonts/CalibreWeb-Light.woff") format("woff");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Calibre-Medium";
  src: url("/consumer/fonts/CalibreWeb-Medium.woff") format("woff");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

The EOT files are not needed for CKAN 2.12's supported browsers. A consumer must
keep its font licence and attribution with the deployment.

## Shared templates and layouts

The shared header keeps CKAN's account controls, responsive menu and site search.
It combines `ckan.site_logo` with `ckan.site_title`. The footer supplies the
established three-column AuScope contact, NCRIS funding and community content plus
the shared acknowledgement. The homepage places the CKAN search across the full
container and leaves the two lower columns available through CKAN's `promoted` and
`featured_organization` blocks. Ordinary pages continue to use CKAN's unmodified
`page.html`, including its skip link, breadcrumb and responsive sidebar.

The shared CSS treats CKAN's `body` as a minimum-viewport-height flex column. The
footer remains in normal document flow, but its automatic block-start margin moves
it to the viewport bottom when a page is short. Long pages grow normally, and the
same Bootstrap `.container` widths continue across the header, ordinary content,
homepage sections and footer.

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
  `auscope_footer_funding_branding`, `auscope_footer_community`,
  `auscope_footer_community_links`, `auscope_footer_social_links` and
  `auscope_footer_acknowledgement` in `footer.html`. `auscope_footer_meta` retains
  CKAN's `footer_attribution` and `footer_lang` names as opt-in blocks.
- `search`, `promoted`, `featured_group` and `featured_organization` in
  `home/index.html`.
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

### Reusable UI components

[Shared form page UI](docs/form-page.md) documents the opt-in stage indicator,
form header and layout, navigation and action row. See
[shared form groups](docs/form-groups.md) for disclosure sections.

Use CKAN's built-in dataset/resource cards, organisation/group snippets and
Bootstrap button, alert and badge classes by default. Core does not wrap those
APIs. The reference review and exclusions are recorded in
[docs/ui-component-analysis.md](docs/ui-component-analysis.md).

Sample and PIDINST both need a compact multi-value facet in some searches. Core
provides an opt-in, JavaScript-free version under its namespace:

```jinja
{% snippet 'snippets/auscope_core/facet_select.html',
  name='tags',
  title=_('Keywords'),
  search_facets=search_facets,
  hide_empty=true
%}
```

Pass `items` instead of `search_facets` when a consumer already has facet items.
Optional arguments are `action`, `query_args` (an iterable of key/value pairs),
`label_function`, `count_label`, `select_label`, `help_text`, `apply_label`,
`empty_message` and `classes`. The component keeps every current query value except
its own facet and `page`, so applying a changed filter returns to the first result
page. It uses a native multiple select and explicit submit button, works without
JavaScript, and inherits Core's design tokens through Bootstrap classes.

Consumers can override
`snippets/auscope_core/facet_select.html` from their own template directory if the
markup genuinely needs to differ. Data and RAiD should retain CKAN's native
`snippets/facet_list.html` unless they establish the same multi-select use case.

Data, Sample, PIDINST and RAiD should set their own `ckan.site_title`, override the
navigation block with routes supplied by their plugins, and override only footer or
homepage blocks whose content differs. The core intentionally does not provide AAF
routes, contact forms, instrument/platform routes, annual reporting links or
repository-specific homepage copy. A consumer may add approved NCRIS artwork in
`auscope_footer_funding_branding`; it must also record the asset licence.

## Geographic validation API

The pure Python API is available from
`ckanext.auscope_core.logic.validators`. It has no CKAN, Shapely or
`ckanext-spatial` dependency:

```python
from ckanext.auscope_core.logic.validators import (
    GeographicValidationError,
    parse_bounding_box,
    validate_geojson,
)

bounds = parse_bounding_box("110,-45,155,-10")
# (110.0, -45.0, 155.0, -10.0), in west/south/east/north order

try:
    location = validate_geojson(
        submitted_location,
        expected_geometry_type="Point",
    )
except GeographicValidationError as error:
    # A consumer maps this message to its own Scheming/NAVL error structure.
    add_consumer_error(str(error))
```

Public functions are:

- `parse_latitude` and `parse_longitude`, which return a finite `float` or raise
  `GeographicValidationError`;
- `is_valid_latitude` and `is_valid_longitude`, which provide boolean checks;
- `validate_position`, for GeoJSON longitude/latitude ordering and optional finite
  additional dimensions;
- `parse_bounding_box` and `is_valid_bounding_box`, accepting
  `west,south,east,north` strings, four-item sequences and the legacy one-item list
  containing a string; and
- `validate_geojson` and `is_valid_geojson`, supporting Point and Polygon geometry
  objects, Features and non-empty FeatureCollections. An expected geometry type can
  be enforced explicitly.

Bounding boxes require `west < east` and `south < north`. Antimeridian-crossing
boxes such as `170,-10,-170,10` are rejected; longitude values are never wrapped or
transformed. Polygon rings must contain at least four positions and be closed.

Consumers decide when to call these functions and retain responsibility for field
requiredness, `noLocation` clearing, elevation, CRS/EPSG policy, coordinate
transformation, feature cardinality and spatial-index updates. Data, Sample,
PIDINST and RAiD can therefore wrap this API in their existing Scheming validators
without changing their stored schema contracts. No consumer has been migrated yet.

## Shared vocabularies and ROR

Core provides small Python clients for ANZSRC 2020 Fields of Research and EPSG
coordinate reference systems. External calls have fixed connect/read timeouts,
bounded streamed responses, bounded results and validated response shapes. The
normalized entry contract is:

```json
{
  "id": "3705",
  "label": "Geology",
  "description": "This group covers geology.",
  "vocabulary": "ANZSRC 2020 Fields of Research"
}
```

`description` is omitted when the provider supplies none. Identifiers are always
strings: FOR keeps the authoritative ANZSRC notation and EPSG keeps the numeric
code without integer conversion in the public result.

Python consumers can use the clients independently of their schema:

```python
from ckanext.auscope_core.services.vocabulary import (
    EpsgVocabularyClient,
    ForVocabularyClient,
)

for_entries = ForVocabularyClient().search("geology", limit=10)
for_entry = ForVocabularyClient().lookup("3705")
epsg_entries = EpsgVocabularyClient().search("Australian", limit=10)
epsg_entry = EpsgVocabularyClient().lookup("EPSG:4326")
```

The enabled plugin also exposes read-only browser APIs:

```text
GET /api/auscope-core/v1/vocabularies/for?q=geology&limit=10
GET /api/auscope-core/v1/vocabularies/for/3705
GET /api/auscope-core/v1/vocabularies/epsg?q=Australian&limit=10
GET /api/auscope-core/v1/vocabularies/epsg/EPSG:4326
```

Search responses contain `{"items": [...]}` and lookup responses contain
`{"item": {...}}`. Invalid input is `400`, missing identifiers are `404`, invalid
upstream responses are `502`, and provider connection failures/timeouts are `503`.
Provider diagnostics and URLs are not returned to callers.

### ROR organisation lookup

The read-only ROR v2 client supports global name search and exact lookup.
It canonicalizes a short ID, a `ror.org/<id>` identifier, or an HTTPS ROR URL,
and verifies the ROR checksum. Python consumers can import
`RorClient` and `normalize_ror_id` from
`ckanext.auscope_core.services.vocabulary.ror`.

```text
GET /api/auscope-core/v1/vocabularies/ror?q=university&limit=10
GET /api/auscope-core/v1/vocabularies/ror/01nfmeh72
GET /api/auscope-core/v1/vocabularies/ror/lookup?id=https%3A%2F%2Fror.org%2F01nfmeh72
```

Results use the same search and lookup envelopes as FOR and EPSG.
Each ROR result includes its canonical `id`, display `label`, `vocabulary`,
`status`, and optional country names in `description`. Search and pasted-ID
suggestions return active organisations. Exact lookup also returns inactive
and withdrawn records with their registry status. ROR rate limits and
connection failures map to `503`. Searches use one upstream page and never
fetch parent records. Enable `auscope_core` and allow the CKAN server to reach
`https://api.ror.org`. Configure a trusted alternate endpoint with
`ckanext.auscope_core.vocabulary.ror.base_url` for testing or a managed mirror.

### Opt-in vocabulary picker

Consumers can render the reusable picker directly from a form template. It uses
CKAN 2.12.1's bundled jQuery and Select2 4. It includes its JavaScript bundle on
pages that render the snippet. The main field submits one identifier or
comma-separated identifiers; optional output mappings write consumer-owned hidden
fields.

FOR multi-select with the established code and JSON-label split:

```jinja
{% snippet 'snippets/auscope_core/vocabulary_picker.html',
  name='fields_of_research_code',
  label=_('Fields of Research'),
  vocabulary='for',
  multiple=true,
  minimum_input_length=3,
  initial_values=for_initial_values,
  output_fields=[{
    'name': 'fields_of_research',
    'source': 'label',
    'format': 'json',
    'initial': data.fields_of_research
  }],
  help_text=_('Search by ANZSRC 2020 FOR code or label.')
%}
```

`for_initial_values` is constructed by the consumer from its stored codes and
label snapshots, for example `[{'id': '3705', 'label': 'Geology'}]`. This makes
the edit form display correctly without changing stored records.

EPSG single-select with separate numeric code and readable label fields:

```jinja
{% snippet 'snippets/auscope_core/vocabulary_picker.html',
  name='epsg_code',
  label=_('Coordinate reference system'),
  vocabulary='epsg',
  initial_values=[{'id': data.epsg_code, 'label': epsg_name}],
  output_fields=[{
    'name': 'epsg',
    'source': 'display',
    'format': 'first',
    'initial': data.epsg
  }],
  placeholder=_('Search by EPSG code or CRS name')
%}
```

For ROR, set `vocabulary='ror'` and supply one stored `{id, label}` value,
or an empty list for a new selection. An empty label displays the stored URL.
Map a hidden output from `label` to persist a display snapshot. Rendering a saved
selection requires no provider request. In an AuScope Composite subfield, pass
the flattened input name and unique ID supplied by the row adapter. The picker
refreshes its accessible references when a row is reindexed and handles row
clear and removal through Composite events. The picker creates an unnamed
Select2 control and persists values through the named hidden inputs.
Its Webassets bundle preloads CKAN's `base/main` for the module loader and Select2.

Each output mapping accepts a consumer field `name`, a `source` (`id`, `label`,
`display`, or the normalized `selection` object), and a `format` (`first`, `csv`,
or `json`). An optional `initial` value preserves the existing hidden-field value
until enhancement completes. The picker does not validate or migrate the consumer
schema. Consumers remain responsible for server-side membership validation,
requiredness, allowed FOR hierarchy/CRS types, defaults and constructing initial
`{id, label}` values.

`minimum_input_length` defaults to `2` and is clamped to at least `1`, because the
Core search API deliberately rejects empty queries. `limit` defaults to `20` and
must not exceed the server's configured maximum.

Search is debounced and bounded, with accessible loading/no-result/error messages,
keyboard navigation, clear/remove behavior, duplicate suppression and stale
response protection. The current API has no pagination metadata, so the picker
shows only the bounded first page and asks users to refine the query; it does not
fake pagination. See
[docs/shared-vocabulary-picker-review.md](docs/shared-vocabulary-picker-review.md)
for legacy storage details and adoption guidance.

Defaults can be changed through declared CKAN options:

| Option | Default |
|---|---|
| `ckanext.auscope_core.vocabulary.ror.base_url` | `https://api.ror.org/v2/organizations` |
| `ckanext.auscope_core.vocabulary.connect_timeout_seconds` | `3` |
| `ckanext.auscope_core.vocabulary.read_timeout_seconds` | `10` |
| `ckanext.auscope_core.vocabulary.default_limit` | `20` |
| `ckanext.auscope_core.vocabulary.max_limit` | `50` |
| `ckanext.auscope_core.vocabulary.max_response_bytes` | `1000000` |
| `ckanext.auscope_core.vocabulary.for.base_url` | ARDC ANZSRC 2020 FOR LDA API |
| `ckanext.auscope_core.vocabulary.for.concept_base_uri` | ANZSRC 2020 FOR concept URI |
| `ckanext.auscope_core.vocabulary.epsg.base_url` | EPSG Registry API v1 |

There is no server-side cache or retry policy in this stage. Consumers retain
their schema mappings, allowed hierarchy/CRS-type policy and stored label
snapshots. The legacy `/api/proxy/fetch_*` routes are intentionally not registered
by Core. See
[docs/shared-for-epsg-vocabulary-review.md](docs/shared-for-epsg-vocabulary-review.md)
for the implementation comparison and migration boundary.

CKAN validates these options during startup: timeouts, limits and the response byte
limit must be positive; the default limit cannot exceed the maximum; and provider
URLs must be non-empty HTTP or HTTPS base URLs. The Python clients apply the same
checks during construction. Invalid deployment configuration therefore fails
before requests are served.

## Visual check

With the development stack running:

1. Set `CKAN__SITE_TITLE=AuScope Data Repository` (or another repository name),
   then open http://localhost:5000/, `/dataset`, `/user/login` and `/about`. Expect a
   light grey masthead with the AuScope icon and title and no decorative border, a
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

The vocabulary picker has dependency-free Node tests for result mapping,
serialization, failures and stale requests:

```bash
node --test --test-isolation=none ckanext/auscope_core/tests/js/vocabulary-picker.test.js
```

## Linting

```bash
pip install -r dev-requirements.txt
ruff check .
```

## Project structure

```
ckanext-auscope-core/
├── AGENTS.md                    # AI development instructions (canonical rules)
├── docs/                        # Architecture, decisions, baselines and analyses
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
        │   └── snippets/auscope_core/ # page_section, facet_select, vocabulary_picker
        ├── public/auscope_core/
        │   ├── images/          # AuScope logos and favicon
        │   └── ASSETS-LICENSES.md
        ├── assets/              # Webassets library "auscope_core"
        │   ├── webassets.yml
        │   ├── css/             # tokens.css, base.css, components.css, branding.css
        │   └── js/              # shared and opt-in CKAN modules
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
- [docs/ui-component-analysis.md](docs/ui-component-analysis.md): Issue #4
  comparison, extracted component and deliberate exclusions
- [docs/shared-for-epsg-vocabulary-review.md](docs/shared-for-epsg-vocabulary-review.md):
  FOR/EPSG reference comparison, providers and shared boundary
- [docs/shared-vocabulary-picker-review.md](docs/shared-vocabulary-picker-review.md):
  legacy picker behaviour, storage mappings and adoption guidance
