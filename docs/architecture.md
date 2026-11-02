# Architecture

## Overview

`ckanext-auscope-core` is a CKAN 2.12.1 extension that holds the frontend pieces the
AuScope repositories have in common. Each repository keeps its own extension for
schemas, business logic and repository-specific pages, and enables `auscope_core`
alongside it.

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

## Plugin

`ckanext.auscope_core.plugin:AuscopeCorePlugin`, registered under the
`ckan.plugins` entry point as `auscope_core`.

Interfaces used now:

| Interface | Purpose |
|---|---|
| `IConfigurer.update_config` | `add_template_directory("templates")`, `add_public_directory("public")`, `add_resource("assets", "auscope_core")` |

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

## Static files and Webassets

- `public/` is served at the site root (registered in CKAN's
  `plugin_public_paths`).
- `assets/` is the Webassets library `auscope_core`. Bundles defined in
  `assets/webassets.yml` are referenced as `auscope_core/<bundle>`, for example
  `{% asset 'auscope_core/auscope_core-css' %}`.
- The current `auscope_core-css` and `auscope_core-js` bundles are placeholders.
  No template includes them yet, so the UI is unchanged.

## Configuration

No configuration options yet. Future options must be declared through CKAN's config
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
variable support and ckanext-envvars.
The database initialisation script passes role names and passwords through psql
variables with identifier/literal quoting. Connection URLs must still percent-encode
reserved characters in passwords.

## Testing

pytest runs inside the `ckan-dev` container with CKAN core's pytest plugin.
`test.ini` inherits CKAN's `test-core.ini`, whose `TEST_CKAN_*` values the image
fills in at start-up. It explicitly overrides `solr_url` with the `solr-test`
service because commands that bypass the image start script do not rewrite CKAN's
core test configuration. Tests check the entry point, plugin loading, template and
public directory registration, the Webassets definitions, `status_show` and home
page rendering. CI rewrites the hostname to its own test-only `solr` service,
installs the built package non-editably, verifies its entry point and packaged
runtime directories, runs the installed suite in `ckan/ckan-dev:2.12.1`, and lints
with ruff.
