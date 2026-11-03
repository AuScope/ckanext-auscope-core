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
`test.ini` inherits CKAN's `test-core.ini` and overrides `solr_url` with the
`solr-test` service. CKAN applies the `CKAN_SQLALCHEMY_URL`, `CKAN_SOLR_URL` and
`CKAN_REDIS_URL` environment variables over both files, and the container sets them
to the development services. Test commands therefore run through
`docker/ckan/test-env.sh`, which swaps in the `TEST_CKAN_*` values (`ckan_test`,
`solr-test`, Redis database 2) and refuses to run if any of them is missing or
equals its development value (ADR-019). Tests check the entry point, plugin
loading, template and public directory registration, the Webassets definitions,
`status_show` and home page rendering. CI rewrites the hostname to its own
test-only `solr` service, installs the built package non-editably, verifies its
entry point and packaged runtime directories, runs the installed suite in
`ckan/ckan-dev:2.12.1`, and lints with ruff.

Only CKAN 2.12.1 has been exercised so far. Issue #5 contains the planned
multi-version matrix. CKAN 2.11.4 and 2.10.1 remain unverified until their matrix
jobs or migration evaluation run successfully; documentation and release metadata
must not imply otherwise.
