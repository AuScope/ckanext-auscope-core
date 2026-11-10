# Architecture

## Overview

`ckanext-auscope-core` holds the frontend pieces the AuScope CKAN repositories have
in common. Each repository keeps its own extension for schemas, business logic and
repository-specific pages, and enables `auscope_core` alongside it. The extension is
developed primarily for CKAN 2.12.1 while retaining a single codebase for older
AuScope CKAN versions where the shared implementation can be verified.

Consumers: Data Repository, Sample Repository, Instrument Registry (PIDINST),
RAiD Repository.

## Layering

```
repository-specific extension   (e.g. Data, Sample, PIDINST, RAiD themes and schemas)
        │ overrides / extends
        ▼
auscope_core                    (shared templates, snippets, assets, static files)
        │ overrides / extends
        ▼
CKAN 2.12.1 core                (never modified)
```

## CKAN compatibility strategy

| CKAN version | Role | Policy |
|---|---|---|
| 2.12.1 | Primary target | Development baseline and required release check; currently verified by the Issue #1 test record |
| 2.11.4 | Secondary target | Required for PIDINST, but compatibility remains unverified until the full integration suite passes on this exact version |
| 2.10.1 | Legacy target | Evaluate when Data and Sample migrate; do not advertise support before that evaluation passes |

The project maintains one implementation across these versions where practical.
Code uses public CKAN extension APIs shared by the targets. Compatibility wrappers,
conditional imports and version checks are introduced only in response to a proven
incompatibility and must be exercised by version-specific tests. A newer API is not
backported pre-emptively, and the primary target is not constrained merely to retain
an unused legacy pattern.

The package currently requires Python 3.10 or newer. CKAN 2.11.4 supports Python
3.9+, and CKAN 2.10.1 supports Python 3.7+, so deployments of those CKAN versions on
Python 3.9 or older cannot install this package under the current policy. This is an
environment constraint, not evidence that the extension works on the remaining
version combinations.

### Current implementation review

The minimal plugin uses APIs available in all three target versions:

- `SingletonPlugin` with `IConfigurer.update_config`;
- `toolkit.add_template_directory` and `toolkit.add_public_directory`, which populate
  `plugin_template_paths` and `plugin_public_paths`;
- `toolkit.add_resource` and `assets/webassets.yml`; CKAN 2.10.1 requires the `.yml`
  filename, while later versions also accept `.yaml`; and
- `CKANConfig` from `ckan.common` for the method annotation.

No compatibility abstraction is needed in the plugin today. The main future risk is
template drift between CKAN releases: every core template override and block name
must be exercised against each supported version. Webassets bundle registration and
rendered asset URLs must likewise be tested in CKAN, not inferred from YAML parsing.
Tests may inspect `plugin_template_paths`, `plugin_public_paths` and
`computed_template_paths`, which are present in the reviewed versions, but rendered
page and asset-loading tests are the compatibility contract.

## Plugin

`ckanext.auscope_core.plugin:AuscopeCorePlugin`, registered under the
`ckan.plugins` entry point as `auscope_core`.

Interfaces used now:

| Interface | Purpose |
|---|---|
| `IConfigurer.update_config` | `add_template_directory("templates")`, `add_public_directory("public")`, `add_resource("assets", "auscope_core")`; replaces `ckan.site_logo` / `ckan.favicon` with the AuScope files only when they equal CKAN's defaults (ADR-023) |

Interfaces that may be added later, only for needs shared by all consumers:
`ITemplateHelpers` (shared helpers), `IBlueprint` (shared pages),
`IConfigDeclaration` (declared config options).

## Plugin order and template resolution

CKAN searches template directories in plugin order: plugins listed earlier in
`ckan.plugins` take priority, and CKAN core templates come last. Consumers should
list their repository-specific plugin before `auscope_core`:

```ini
ckan.plugins = <repository_theme> auscope_core <other plugins> envvars
```

`envvars` stays last, as its documentation requires.

## Template inheritance

- Extend core templates with `{% ckan_extends %}` and override the smallest block
  that does the job. Do not copy whole core templates.
- Put reusable shared snippets under `templates/snippets/auscope_core/` so their
  names cannot clash with core or consumer snippets.
- Keep core template overrides few; each one adds upgrade work.

Current overrides and their deliberately small scope:

| Template | Shared responsibility | Consumer extension points |
|---|---|---|
| `base.html` | Include shared CSS after CKAN's bundle | `auscope_core_styles` |
| `header.html` | Render `ckan.site_logo` beside `ckan.site_title` | AuScope brand blocks and CKAN's account/navigation/search blocks |
| `footer.html` | Established Contact Us, NCRIS funding, community and acknowledgement content | Fine-grained `auscope_footer_*` blocks; CKAN `footer_attribution` / `footer_lang` names remain opt-in |
| `home/index.html` | Full-width search followed by two responsive content columns | CKAN's `search`, `promoted`, `featured_group`, `featured_organization` |

`page.html` is intentionally not overridden. CKAN 2.12.1 already provides the
skip link, breadcrumb, responsive primary/secondary columns and standard page
blocks. Consumers use those blocks directly. The
`snippets/auscope_core/page_section.html` macro provides reusable CKAN `module`,
`module-heading` and `module-content` markup for repository-specific pages.

## Static files and Webassets

- `public/` is served at the site root (registered in CKAN's
  `plugin_public_paths`). Shared files live under `public/auscope_core/`, so they
  are served at `/auscope_core/...` and cannot clash with consumers' `/base/...`
  files (ADR-026).
- `assets/` is the Webassets library `auscope_core`. Bundles defined in
  `assets/webassets.yml` are referenced as `auscope_core/<bundle>`, for example
  `{% asset 'auscope_core/auscope_core-css' %}`.

## Styling architecture

The theme is plain CSS layered over CKAN 2.12.1's unmodified `main.css`
(Bootstrap 5). There is no Sass or Node build step (ADR-021).

| Layer | File | Role |
|---|---|---|
| Design tokens | `assets/css/tokens.css` | `--auscope-*` custom properties on `:root`: palette (with `-rgb` triplets), semantic colours, typography, focus ring, component values. The public customisation API. |
| Bootstrap mapping | `assets/css/base.css` | Assigns tokens to the `--bs-*` variables CKAN reads (`:root, [data-bs-theme=light]`); established AuScope type scale; prose-link underlines; `:focus-visible` outlines; skip link; `prefers-reduced-motion`. |
| Components | `assets/css/components.css` | `--bs-btn-*`, `--bs-nav-pills-*`, `--bs-pagination-*` for primary buttons, pills and pagination; checked and focused form controls. |
| Branding | `assets/css/branding.css` | Targeted rules for CKAN components with hard-coded colours: page surface, masthead, logo size, masthead nav states, toggler, account bar, footer, homepage search. |

Bundles: `auscope_core-tokens` (tokens only) and `auscope_core-css` (base,
components, branding, with `extra.preload: [auscope_core/auscope_core-tokens]`).
CKAN's `include_asset` emits preloaded bundles first and only once.
`auscope_core-js` is registered but not included (ADR-022).

Inclusion: `templates/base.html` extends core with `{% ckan_extends %}` and, in
`{% block styles %}`, renders `{{ super() }}` (core `main.css`) followed by the
named block `auscope_core_styles`, which includes `auscope_core-css`. Load order is
therefore core `main.css`, tokens, shared CSS, consumer bundles, then
`ckan.site_custom_css`. Equal-specificity rules in the shared CSS win over core by
order; selectors that compete with more specific CKAN rules state their specificity
in comments.

Rules that keep the theme accessible (ADR-025): brand values only in
`tokens.css`; prose links underlined; focus outlines never removed, with one
`:focus-visible` selector per CKAN `outline: 0` rule on a rendered component;
containers with their own colour scheme (`.site-footer`, the homepage
`.homepage .module-search .tags` strip) set `--auscope-focus-ring-color` and
`--bs-heading-color` to explicit `var(...)` values; teal is decorative only.
`tests/test_theme_css.py` checks token contrast (WCAG AA) and these rules
statically.

The intended look (surfaces, footer, homepage search, typography) and the
deliberate differences from the legacy sites are in
[design-baseline.md](design-baseline.md).

Consumers customise styling by overriding tokens in a later-loaded bundle, by
`ckan.site_custom_css`, by overriding `auscope_core_styles`, or through
`ckan.site_logo` / `ckan.favicon` (README "Theme and branding"). Brand assets and
their licences are listed in `public/auscope_core/ASSETS-LICENSES.md`.
The font tokens prefer the legacy `Calibre-light` and `Calibre-Medium` family names,
but Core contains no `@font-face` URLs or binaries. Licensed consumers supply those
faces in their own later-loaded bundle; otherwise the token fallbacks are used.
The `body` background uses the footer token to cover space below short pages without
changing Bootstrap's `--bs-body-bg`, which would also recolour controls.

## Configuration

No configuration options of its own. The plugin changes the defaults of
`ckan.site_logo` (to the AuScope icon) and `ckan.favicon` only when CKAN's defaults
are still in effect. The shared header uses CKAN's `ckan.site_title` for the
repository name. Navigation and repository-specific content are template blocks,
because their destinations belong to consumer plugins rather than configuration
data. Future AuScope-specific options must be declared through CKAN's config
declaration (`IConfigDeclaration`) with the `ckanext.auscope_core.` prefix.

## Out of scope

Business logic, repository-specific schemas (e.g. scheming YAML), metadata
validators, harvesters, DOI/IGSN/RAiD integrations and CKAN core changes.

## Development environment

`docker-compose.yml` runs `ckan-dev` (built from `docker/ckan/Dockerfile.dev`, based
on `ckan/ckan-dev:2.12.1`), `db` (`postgres:15-alpine`), separate `solr` and
`solr-test` services (`ckan/ckan-solr:2.12-solr9`) and `redis` (`redis:7-alpine`).
The extension is installed editable at build time and the repository is bind-mounted
over the same path at `/srv/app/src_extensions/ckanext-auscope-core`.
`docker/postgres/initdb`
creates the CKAN role and the `ckan_default` and `ckan_test` databases. Configuration
comes from `.env` (copied from `.env.example`) through the image's environment
variable support and ckanext-envvars. The example sets `CKAN__SITE_TITLE` to an
explicit development title so the shared icon/title header is visible immediately;
consumer deployments replace it with their repository name.
The database initialisation script passes role names and passwords through psql
variables with identifier/literal quoting. Connection URLs must still percent-encode
reserved characters in passwords.

## Testing

pytest runs inside the `ckan-dev` container with CKAN core's pytest plugin.
`test.ini` inherits CKAN's `test-core.ini` and overrides `solr_url` with the
`solr-test` service. CKAN applies the `CKAN_SQLALCHEMY_URL`, `CKAN_SOLR_URL` and
`CKAN_REDIS_URL` environment variables over both files, and the container sets them
to the development services. Test commands therefore run through
`docker/ckan/test-env.sh`, which swaps in the `TEST_CKAN_*` values (`ckan_test`,
`solr-test`, Redis database 2) and refuses to run if any of them is missing or
equals its development value (ADR-019). Tests check the entry point, plugin
loading, template and public directory registration, the Webassets definitions,
`status_show` and home page rendering (`test_plugin.py`). `test_theme.py` checks
bundle registration, the rendered stylesheet order, that the CSS and images are
served, and the logo and favicon default rule. `test_theme_css.py` is pure Python:
token definitions, contrast pairs, `-rgb` triplets, dark-surface and focus rules,
and licence entries for every image. CI rewrites the hostname to its own test-only
`solr` service. `test_layouts.py` renders the home, dataset list, dataset detail and
login pages; checks the common landmarks and responsive grid; and verifies the
consumer block and macro contracts. CI installs the built package non-editably,
verifies its entry point and packaged runtime directories, runs the installed suite in
`ckan/ckan-dev:2.12.1`, and lints with ruff.

Only CKAN 2.12.1 has been exercised so far. Issue #5 contains the planned
multi-version matrix. CKAN 2.11.4 and 2.10.1 remain unverified until their matrix
jobs or migration evaluation run successfully; documentation and release metadata
must not imply otherwise.
