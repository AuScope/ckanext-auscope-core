# Tech

- CKAN 2.12.1. Python >= 3.10; the dev image runs Python 3.14.
- Packaging follows the CKAN 2.12.1 extension cookiecutter: metadata and the
  `ckan.plugins` entry point in `pyproject.toml`, Babel settings in `setup.cfg`,
  `message_extractors` in `setup.py`. Build backend setuptools >= 64.
- Plugin interfaces: `IConfigurer` now (also sets the `ckan.site_logo` /
  `ckan.favicon` defaults when CKAN's defaults are in effect). Add others (e.g.
  `ITemplateHelpers`, `IBlueprint`, `IConfigDeclaration`) only for needs shared by
  all consumers.
- Templates: Jinja2 with `{% ckan_extends %}`; override the smallest block. The only
  core override is `templates/base.html` (block `auscope_core_styles`).
- Assets: Webassets library `auscope_core` in `assets/webassets.yml`; bundles are
  referenced as `auscope_core/<bundle>`: `auscope_core-tokens`, `auscope_core-css`
  (preloads tokens) and `auscope_core-js` (placeholder, not included).
- Styling: plain CSS custom properties over CKAN's Bootstrap 5 `main.css`, no build
  step. Styling rules: AGENTS.md.
- Tests: pytest with CKAN core's pytest plugin and fixtures (`with_plugins`,
  `clean_db`, `app`), configured by `test.ini`.
- Lint: ruff 0.17.3 (rules E, F, W; line length 88).
- Dev stack (Docker or Podman Compose): `ckan/ckan-dev:2.12.1`,
  `postgres:15-alpine`, `ckan/ckan-solr:2.12-solr9`, `redis:7-alpine`.

Commands: AGENTS.md. Rationale: docs/decisions.md.
