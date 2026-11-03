# Decisions

Architecture decision log. Each entry records context, decision and consequences.
Add new entries at the end; mark replaced entries as `Superseded by ADR-NNN`.

## Verified CKAN 2.12.1 facts

Checked on 2026-11-02 while setting up Issue #1.

| Fact | Value | Source |
|---|---|---|
| Python requirement | `python_requires >= 3.10`; classifiers 3.10 to 3.12 | [ckan-2.12.1 setup.cfg](https://raw.githubusercontent.com/ckan/ckan/ckan-2.12.1/setup.cfg) |
| Supported Python range (docs) | CKAN 2.12 supports Python 3.10 to 3.14 | [installing/index.rst](https://github.com/ckan/ckan/blob/master/doc/maintaining/installing/index.rst) |
| PostgreSQL | 12 or newer | [Install from source (2.12)](https://docs.ckan.org/en/2.12/maintaining/installing/install-from-source.html) |
| CKAN's own CI services | `postgres:14`, `redis:7`, Python 3.10 | [ckan-2.12.1 pytest.yml](https://github.com/ckan/ckan/blob/ckan-2.12.1/.github/workflows/pytest.yml) |
| Core pins | Flask 3.1.3, Jinja2 3.1.6, webassets 3.0.0, SQLAlchemy 2.0.51; dev: pytest 9.1.1, pytest-cov 7.1.0 | [requirements.in](https://raw.githubusercontent.com/ckan/ckan/ckan-2.12.1/requirements.in), dev-requirements.txt |
| pytest plugin | CKAN core registers `ckan.tests.pytest_ckan.ckan_setup` and `.fixtures` as `pytest11` entry points | ckan-2.12.1 setup.cfg |
| Extension template | `contrib/cookiecutter/ckan_extension`: pyproject.toml, minimal setup.cfg/setup.py, test.ini, IConfigurer plugin, CI workflow | [cookiecutter at ckan-2.12.1](https://github.com/ckan/ckan/tree/ckan-2.12.1/contrib/cookiecutter/ckan_extension) |
| Dev image | `ckan/ckan-dev:2.12.1` (same digest as `2.12` and `2.12.1-py3.14`: `sha256:4f21dd73d19039cc91a43ed98635b91b31219de070d21161a380fc0829a971d0`) | [Docker Hub tags](https://hub.docker.com/v2/repositories/ckan/ckan-dev/tags?name=2.12) |
| Dev image internals | Debian `python:3.14-slim-bookworm`; CKAN source `/srv/app/src/ckan`; `SRC_EXTENSIONS_DIR=/srv/app/src_extensions`; runs as `ckan`; writes `TEST_CKAN_*` into `test-core.ini` at start-up; has `curl` | [ckan-docker-base/ckan-2.12](https://github.com/ckan/ckan-docker-base/tree/main/ckan-2.12) |
| Solr image | `ckan/ckan-solr:2.12-solr9` | Docker Hub |
| CI Postgres image | `ckan/ckan-postgres-dev:2.12` (`ckan_default`/`pass`, db `ckan_test`, base `postgres:15-alpine`) | [ckan-postgres-dev](https://github.com/ckan/ckan-postgres-dev) |
| Webassets loader | Reads `webassets.yaml` or `webassets.yml` from the `add_resource` directory; bundles named `<library>/<bundle>` | ckan-2.12.1 `ckan/lib/webassets_tools.py` |
| Template paths | Final search list in `config["computed_template_paths"]` | ckan-2.12.1 `ckan/config/environment.py` |
| Public paths | `add_public_directory` appends to `config["plugin_public_paths"]` (a list); `extra_public_paths` holds only the configured value; Flask serves both | ckan-2.12.1 `ckan/plugins/toolkit.py`, `ckan/config/middleware/flask_app.py` (read in the running container) |
| ruff | 0.17.3 (latest at setup time) | [PyPI](https://pypi.org/pypi/ruff/json) |

---

## ADR-001: Packaging follows the CKAN 2.12.1 cookiecutter

- Date: 2026-11-02. Status: Accepted.
- Context: CKAN 2.12.1 ships an official extension template. Older AuScope
  extensions keep all metadata in `setup.cfg`.
- Decision: `pyproject.toml` holds all metadata and the `ckan.plugins` entry point.
  `setup.cfg` keeps only `packages`, `namespace_packages`, `include_package_data`,
  the Babel extractor and catalogue sections. `setup.py` keeps only
  `message_extractors`.
- Consequences: matches the target version's template. Babel config cannot move to
  `pyproject.toml` yet. setuptools 84.2.1 prints a deprecation warning for
  `namespace_packages` but builds the wheel; the line is kept because CKAN's
  template and the other `ckanext-*` packages use the same namespace mechanism.

## ADR-002: Names

- Date: 2026-11-02. Status: Accepted.
- Decision: distribution `ckanext-auscope-core`, import package
  `ckanext.auscope_core`, plugin `auscope_core`, class `AuscopeCorePlugin` in
  `ckanext/auscope_core/plugin.py`.

## ADR-003: Python version range

- Date: 2026-11-02. Status: Accepted.
- Decision: `requires-python = ">=3.10"` (CKAN 2.12.1 `python_requires`).
  Classifiers list 3.10 to 3.14 as documented for CKAN 2.12.
- Consequences: only Python 3.14 (dev image) and 3.12 (local wheel build) have been
  exercised. Other versions are declared, not tested.

## ADR-004: No runtime dependencies

- Date: 2026-11-02. Status: Accepted.
- Decision: `dependencies = []`; `requirements.txt` contains only a comment. CKAN is
  not declared as a dependency (CKAN extension convention: the host installs CKAN).
  Build backend `setuptools>=64`, the first version with PEP 660 editable installs.

## ADR-005: Tests use CKAN core's pytest plugin

- Date: 2026-11-02. Status: Accepted.
- Decision: no `pytest-ckan`; CKAN 2.12.1 registers its pytest plugin itself. pytest
  and pytest-cov come from CKAN's dev requirements, preinstalled in `ckan/ckan-dev`.
  `dev-requirements.txt` pins only `ruff==0.17.3`.

## ADR-006: test.ini path

- Date: 2026-11-02. Status: Accepted.
- Decision: `use = config:../../src/ckan/test-core.ini`, which resolves when the
  repository is mounted at `/srv/app/src_extensions/ckanext-auscope-core` in the
  `ckan-dev` container. CI rewrites it to the absolute path with `sed`, as the
  cookiecutter workflow does. Source installs edit the line (README).

## ADR-007: Minimal plugin

- Date: 2026-11-02. Status: Partly superseded by ADR-021 (templates). The
  empty-directory wheel gap is fixed for `templates/` and `public/`, which now hold
  real files; `i18n/` still holds only `.gitkeep`.
- Context: Issue #1 is the skeleton only; styling, branding and UI are separate
  issues.
- Decision: implement only `IConfigurer`. No template overrides, helpers or
  blueprints. `templates/`, `public/` and `i18n/` contain `.gitkeep` only.
- Consequences: enabling the plugin does not change the UI. Empty directories are
  not packaged into a wheel (only editable installs have them). A non-editable
  install with these directories missing has not been tested; the issue goes away
  once the directories hold real files.

## ADR-008: Placeholder Webassets bundles

- Date: 2026-11-02. Status: Superseded by ADR-021.
- Decision: `assets/webassets.yml` defines `auscope_core-css` and `auscope_core-js`,
  each pointing to a comment-only file. No template includes them.
- Consequences: establishes the bundle naming convention (`auscope_core/<bundle>`)
  and avoids an empty YAML file.

## ADR-009: Docker/Podman development environment

- Date: 2026-11-02. Status: Accepted.
- Decision: root `docker-compose.yml` (project name `ckanext-auscope-core`, no
  `container_name`, fully qualified image names for Podman):
  `docker.io/ckan/ckan-dev:2.12.1` via `docker/ckan/Dockerfile.dev`,
  `docker.io/library/postgres:15-alpine` (same major as `ckan-postgres-dev:2.12`;
  CKAN needs 12+), `docker.io/ckan/ckan-solr:2.12-solr9`,
  `docker.io/library/redis:7-alpine` (CKAN CI uses Redis 7). The extension is
  installed editable at build time and bind-mounted at runtime. Images are pinned by
  tag; the ckan-dev digest is recorded above.
- Consequences: works with `docker compose` and `podman compose` (verified with
  Podman 6.0.2). No database, Solr or Redis ports are published. Avoids the
  reference repositories' fixed container names, which collide between stacks.

## ADR-010: Plugin list and order

- Date: 2026-11-02. Status: Accepted.
- Decision: dev env uses
  `CKAN__PLUGINS="auscope_core image_view text_view datatables_view envvars"`.
  `datastore` is dropped from the image default so no datastore database is needed.
  `envvars` is last, as its README requires. Consumers list their
  repository-specific plugin before `auscope_core`, because earlier plugins take
  template priority.

## ADR-011: License not set

- Date: 2026-11-02. Status: Open.
- Context: the repository has no LICENSE and none was specified. CKAN and the
  reference extensions use AGPL.
- Decision: no LICENSE file, no `license` field, no license classifier, no
  `include LICENSE` in MANIFEST.in until maintainers choose a license.

## ADR-012: CI workflow

- Date: 2026-11-02. Status: Accepted (verified 2026-11-03).
- Decision: `.github/workflows/test.yml` adapted from the cookiecutter: tests in
  `ckan/ckan-dev:2.12.1` with `options: --user root` (the image user `ckan` cannot
  `pip install`), services `ckan-solr:2.12-solr9`, `ckan-postgres-dev:2.12`,
  `redis:7`; lint with `astral-sh/ruff-action@v3` pinned to ruff 0.17.3.
- Consequences: the YAML parses locally and the same test commands pass in the dev
  container. GitHub Actions run 41433780892 passed both `lint` and `test`, including
  non-editable installation verification, on PR #7.

## ADR-013: AI documentation layout

- Date: 2026-11-02. Status: Accepted.
- Decision: `AGENTS.md` is canonical. `.kiro/steering/*.md` are short and point to
  `AGENTS.md` and `docs/` instead of repeating rules.

## ADR-014: Line endings

- Date: 2026-11-02. Status: Accepted.
- Decision: `.gitattributes` forces LF for `*.sh`, `Dockerfile*`, `*.yml`, `*.yaml`
  and `*.ini`, so scripts run in Linux containers when checked out on Windows.

## ADR-015: Assumptions

- Date: 2026-11-02. Status: Accepted.
- Author name `AuScope`; version `0.1.0`.
- `.env.example` values are throwaway local-development placeholders.
- Dev and test runs use physically separate Solr services and named volumes.
- The PIDINST reference repository was only partly inspected (its compose file
  could not be read).
- CI is verified on GitHub Actions (ADR-012). Only Python 3.14 and 3.12 were
  exercised (ADR-003).

---

## Verification record: Issue #1 (2026-11-02)

Environment: Windows, Python 3.12.5, Podman 6.0.2 (WSL machine), Docker Compose
v2.39.2 as the Podman compose provider. `docker` itself is not installed.

Local (venv with ruff 0.17.3, PyYAML):

| Command | Result |
|---|---|
| `python -m pip wheel --no-deps -w %TEMP%\acore-dist .` | `Successfully built ckanext-auscope-core` (`ckanext_auscope_core-0.1.0-py3-none-any.whl`); setuptools 84.2.1 `namespace_packages` deprecation warning |
| Wheel listing | contains `plugin.py`, `assets/webassets.yml`, css/js files, tests; `entry_points.txt`: `[ckan.plugins] auscope_core = ckanext.auscope_core.plugin:AuscopeCorePlugin` |
| `ruff check .` | `All checks passed!` |
| `yaml.safe_load` of workflow and compose file | `yaml ok` |

Container (CKAN 2.12.1):

| Command | Result |
|---|---|
| `podman compose config` | parsed without errors |
| `podman compose up -d --build` | exit 0; all four services started; `ckan-dev` healthcheck `healthy` |
| `GET http://localhost:5000/api/3/action/status_show` | `ckan_version: 2.12.1`; `extensions: [auscope_core, image_view, text_view, datatables_view, envvars]` |
| `GET http://localhost:5000/` | HTTP 200 |
| `pip show ckanext-auscope-core` (in container) | Version 0.1.0, editable project location `/srv/app/src_extensions/ckanext-auscope-core`; Python 3.14.10 |
| `ckan -c test.ini db init` | `Upgrading DB: SUCCESS` |
| `pytest --ckan-ini=test.ini -p no:cacheprovider -v ckanext/auscope_core` (first run) | 1 failed, 6 passed: `test_public_directory_registered` read `extra_public_paths`, which does not hold plugin dirs in 2.12.1. Test fixed to read `plugin_public_paths`. |
| same command (after fix) | `7 passed in 7.44s` (pytest 9.1.1, plugins include `ckan-2.12.1`, `cov-7.1.0`) |
| `podman compose down` | containers and network removed; volumes kept |

Not verified: the GitHub Actions workflow; Python 3.10, 3.11 and 3.13; installation
into a non-Docker CKAN source install; `docker` (as opposed to Podman) runs.

## ADR-016: Isolate automated tests from development Solr

- Date: 2026-11-02. Status: Accepted.
- Context: CKAN test fixtures clear the configured Solr core. Pointing tests at the
  development service could destroy a developer's search index.
- Decision: Compose runs a dedicated `solr-test` service with its own named volume,
  `.env.example` sets `TEST_CKAN_SOLR_URL` to that service, and `test.ini` explicitly
  overrides `solr_url` with it. The explicit override also protects commands that
  bypass the image's start script. CI rewrites the hostname to its test-only `solr`
  service.
- Consequences: the local stack runs a second Solr container, trading some memory
  and disk use for hard isolation of development data.
- Amended by ADR-019: inside Compose the `test.ini` override alone does not take
  effect, because `CKAN_SOLR_URL` overrides it.

## ADR-017: Quote PostgreSQL init values through psql variables

- Date: 2026-11-02. Status: Accepted.
- Decision: pass the CKAN role and password with `psql --set`, then interpolate them
  with psql's identifier (`:"name"`) and literal (`:'name'`) quoting. Shell argument
  arrays remain responsible for database names.
- Consequences: quotes, dollar signs and other special characters cannot break or
  inject SQL. URI-reserved characters must separately be percent-encoded in CKAN's
  SQLAlchemy connection URLs.

## ADR-018: Verify the non-editable distribution

- Date: 2026-11-02. Status: Accepted.
- Decision: graft all four runtime resource directories into the source manifest.
  CI uses `pip install .`, then loads the installed CKAN entry point and checks the
  asset, i18n, public and template directories from `/tmp`, outside the checkout.
  pytest also runs from `/tmp` with `--pyargs` so it exercises the installed wheel
  rather than importing the source checkout.
- Consequences: empty resource directories (currently represented by tracked
  placeholders) and Webassets definitions are present in wheel installations, not
  only editable source installs.

---

## Verification record: Issue #1 review fixes (2026-11-02)

Environment: Windows host, Podman 6.0.2, CKAN development image Python 3.14.10.

| Check | Result |
|---|---|
| `podman compose config` and `up -d --build` | Parsed and started `db`, `redis`, `solr`, dedicated `solr-test`, and `ckan-dev` |
| `ruff check .` | `All checks passed!` |
| Workflow and Compose YAML parse | Passed with PyYAML in the CKAN container |
| `pip wheel --no-deps -w dist .` | Built `ckanext_auscope_core-0.1.0-py3-none-any.whl` |
| Non-editable wheel verification from `/tmp` | Entry point loaded from site-packages; assets, i18n, public, templates and `webassets.yml` present |
| PostgreSQL init with special-character test password | Role and both databases created; quote, dollar sign, space and backslash handled without exposing the value |
| `ckan -c test.ini db init` | `Upgrading DB: SUCCESS` |
| Installed-package pytest (`--pyargs ckanext.auscope_core`) | `7 passed, 15 warnings in 6.03s` |
| GitHub Actions run 41433780892 on PR #7 | `lint`: success; `test`: success, including non-editable installation verification |

---

## ADR-019: Run tests through a test-connection wrapper

- Date: 2026-11-09. Status: Accepted.
- Assumption: no GitHub issue exists for this. It is an Issue #1 development
  environment follow-up, so the branch is `feature/1-test-db-isolation`.
- Context: running the documented pytest command in Compose emptied the
  development database (`organization_list` returned `[]` after a run). Read in the
  running `ckan/ckan-dev:2.12.1` container:
  - `/srv/app/src/ckan/ckan/config/environment.py`, `CONFIG_FROM_ENV_VARS` (lines
    81-100) maps `sqlalchemy.url`, `solr_url`, `ckan.redis.url` (and datastore,
    site, storage and SMTP options) to `CKAN_*` variables. `update_config()`
    (line 103) copies every non-empty variable into `config` before plugins load,
    so the variables override every ini file. CKAN's own
    `ckan/tests/config/test_environment.py` states that these take precedence over
    the config file. `ckan/tests/pytest_ckan/ckan_setup.py` builds the test app
    with `make_app`, which runs this code.
  - `.env` sets `CKAN_SQLALCHEMY_URL` (`ckan_default`), `CKAN_SOLR_URL` (`solr`) and
    `CKAN_REDIS_URL` (Redis db 1) in the container. Database, Solr and Redis were
    all affected. ADR-016's `solr_url` in `test.ini` was overridden by
    `CKAN_SOLR_URL`, so it never protected the development Solr core in Compose.
  - `/srv/app/start_ckan_development.sh` (lines 29-36) tries to write the
    `TEST_CKAN_*` values into `test-core.ini`, but in this image the file is owned
    by `ckan-sys` with mode 644 and the script runs as `ckan`. The container log
    shows `PermissionError: [Errno 13] Permission denied:
    '/srv/app/src/ckan/test-core.ini'`, so `test-core.ini` keeps its `localhost`
    defaults. Even when that write succeeds, the `CKAN_*` variables still win.
- Options: (a) `-e CKAN_...=...` flags in the documented command: long, repeats the
  database password in the docs and is easy to drop. (b) a separate Compose test
  service: duplicates the `ckan-dev` definition and adds a second container
  start-up for each run. (c) a small checked-in wrapper script.
- Decision: (c). `docker/ckan/test-env.sh` (POSIX `sh`) exports
  `CKAN_SQLALCHEMY_URL`, `CKAN_SOLR_URL` and `CKAN_REDIS_URL` from the matching
  `TEST_*` variables, then `exec`s its arguments. It exits with an error if a test
  value is unset or equals the development value. README and AGENTS.md run both
  `ckan -c test.ini db init` and pytest through it. `test.ini` keeps its
  `solr_url` override for source installs.
- CI: unchanged. `.github/workflows/test.yml` sets the `CKAN_*` variables to its own
  test-only services (`ckan_test`, a Solr service used only by tests, Redis db 1 in a
  throwaway service), so the variables there already point at test data.
- Consequences: the guard caught a real misconfiguration: the local `.env` (created
  before ADR-016) still had `TEST_CKAN_SOLR_URL=http://solr:8983/solr/ckan`. Older
  `.env` files must copy the current value from `.env.example`. `CKAN_SITE_URL` and
  `CKAN_STORAGE_PATH` still override the test config; the current tests write no
  files, so this was left unchanged.

## Verification record: ADR-019 (2026-11-09)

Environment: Windows host, Podman 6.0.2 with Docker Compose v2.39.2 as provider,
`ckan/ckan-dev:2.12.1` (Python 3.14.10). Commands ran from the repository root with
`podman compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev`
(abbreviated `exec`). The probe script loaded `test.ini` with `load_config` and
`make_app` and printed the effective database name, `solr_url` and
`ckan.redis.url`.

| Step | Command | Result |
|---|---|---|
| Start | `podman compose up -d --build` | All five services started; `status_show` returned `ckan_version: 2.12.1` with `auscope_core` |
| Root cause | `exec python /tmp/probe_cfg.py` (no wrapper) | `db: ckan_default`, `solr: http://solr:8983/solr/ckan`, `redis: redis://redis:6379/1` |
| Guard, stale `.env` | `exec sh docker/ckan/test-env.sh python /tmp/probe_cfg.py` | `test-env: TEST_CKAN_SOLR_URL equals CKAN_SOLR_URL; refusing to use development data`, exit 1 |
| Guard, missing value | `exec env -u TEST_CKAN_REDIS_URL sh docker/ckan/test-env.sh true` | `test-env: TEST_CKAN_REDIS_URL is not set; see .env.example`, exit 1 |
| Fix `.env` | Set local `TEST_CKAN_SOLR_URL=http://solr-test:8983/solr/ckan` (the `.env.example` value), `podman compose up -d ckan-dev` | Container recreated |
| Wrapper | `exec sh docker/ckan/test-env.sh python /tmp/probe_cfg.py` | `db: ckan_test`, `solr: http://solr-test:8983/solr/ckan`, `redis: redis://redis:6379/2` |
| Seed dev marker | `podman compose exec ckan-dev python /tmp/seed_marker.py seed` (`/srv/app/ckan.ini`, `organization_create` and `package_create`) | `db: ckan_default`; `orgs: ['isolation-marker-org', 'auscope-branding-check']`; `solr hits: 1` |
| Dev Solr before | `curl "http://solr:8983/solr/ckan/select?q=*:*&rows=0"` | `"numFound":4` |
| Test DB init | `exec sh docker/ckan/test-env.sh ckan -c test.ini db init` | `CKAN database version upgraded: base -> 9445ce34fc23 (head)`, `Upgrading DB: SUCCESS`. `ckan_test` had never been initialised, so earlier test runs used `ckan_default` |
| Tests | `exec sh docker/ckan/test-env.sh pytest --ckan-ini=test.ini -p no:cacheprovider -v ckanext/auscope_core` | `7 passed in 9.56s` (2 tests use `clean_db`) |
| Dev marker after | `podman compose exec ckan-dev python /tmp/seed_marker.py check` | `db: ckan_default`; `orgs: ['isolation-marker-org', 'auscope-branding-check']`; `solr hits: 1` |
| Dev Solr after | same `curl` against `solr` | `"numFound":4` (unchanged) |
| Test Solr after | same `curl` against `solr-test` | `"numFound":0` |
| Lint | `ruff check .` (ruff 0.17.3) | `All checks passed!` |
| Stop | `podman compose down` | Containers removed; volumes kept |

The unwrapped pytest command was not re-run, because it would empty the
development database again. CI was not re-run for this change.

---

## ADR-020: One codebase with tiered CKAN compatibility

- Date: 2026-11-03. Status: Accepted.
- Context: RAiD targets CKAN 2.12.1, PIDINST runs CKAN 2.11.4, and the Data and
  Sample repositories currently run CKAN 2.10.1. Shared frontend code should simplify
  upgrades without implying support that has not been tested.
- Decision: CKAN 2.12.1 is the primary target, 2.11.4 is the secondary target, and
  2.10.1 is a legacy target to evaluate during Data/Sample migration. Maintain one
  implementation using shared public CKAN APIs. Introduce version-specific code only
  for a reproduced incompatibility with test coverage. Compatibility is claimed only
  after the full integration suite passes on the exact CKAN version.
- Consequences: current plugin registration, template/public path helpers,
  `CKANConfig` annotation and `webassets.yml` need no compatibility branches. The
  package's Python >=3.10 requirement excludes older Python environments otherwise
  accepted by CKAN 2.10.1 and 2.11.4. CKAN 2.11.4 and 2.10.1 are not yet verified.

## ADR-020: Plain CSS design tokens layered over CKAN `main.css`

- Date: 2026-11-03. Status: Accepted.
- Context: the reference repositories ship a 23 KB legacy `shared_style.css` that
  redefines Bootstrap variables (`--bs-teal`, `--bs-gray`, `--bs-red`) with new
  meanings. CKAN 2.12.1's Bootstrap 5 build reads `--bs-*` variables at runtime.
- Decision: no Sass rebuild and no `ckan.theme` replacement. Brand values are
  `--auscope-*` custom properties on `:root` in `tokens.css` (with `-rgb` triplets
  where Bootstrap needs them). `base.css` assigns them to the `--bs-*` variables of
  the same meaning; `components.css` and `branding.css` cover components with
  Bootstrap variables or hard-coded CKAN colours. No `url()` in the CSS, so no
  `cssrewrite` filter is needed.
- Consequences: no build toolchain; CKAN upgrades only need the targeted selectors
  re-checked. Consumers that change a colour must also change its `-rgb` companion.
  Some CKAN colours not covered (for example `.btn-default`, the activity stream)
  stay CKAN teal until a consumer needs them.

## ADR-021: Bundles and `base.html` inclusion

- Date: 2026-11-03. Status: Accepted. Supersedes ADR-008; partly supersedes ADR-007
  (templates).
- Decision: bundles `auscope_core-tokens` (tokens only) and `auscope_core-css`
  (base, components, branding; `extra.preload: [auscope_core/auscope_core-tokens]`).
  `auscope_core-js` stays registered as a placeholder and is not included. One core
  override, `templates/base.html`, renders `{{ super() }}` in `{% block styles %}`
  and then the named block `auscope_core_styles` with the `auscope_core-css` asset.
- Consequences: shared CSS loads after `main.css`, tokens are emitted once and first,
  and consumers can replace, reduce to tokens only, or drop the shared styles from
  their own `base.html` without a config option. The integration test on the
  rendered link order catches a renamed core `styles` block.

## ADR-022: Logo and favicon defaults only when CKAN defaults are in effect

- Date: 2026-11-03. Status: Accepted.
- Context: CKAN fills in config defaults before plugins' `update_config` runs, and
  CKAN-generated configs (including the dev `/srv/app/ckan.ini`) set
  `ckan.site_logo = /base/images/ckan-logo.png` and
  `ckan.favicon = /base/images/ckan.ico` explicitly.
- Decision: `update_config` replaces `ckan.site_logo` / `ckan.favicon` with
  `/auscope_core/images/auscope-logo.png` / `auscope-favicon.png` only when the value
  equals CKAN's default. Values are compared rather than checking whether the key is
  set. Any other value, including an empty string, is kept.
- Consequences: `IConfigurer` runs in reverse plugin order, so `envvars` (listed last)
  applies `CKAN__SITE_LOGO` / `CKAN__FAVICON` first and the rule leaves them alone;
  sysadmin values from `system_info` are applied later and also win. To keep CKAN's
  logo, set any other path. The rule is idempotent.

## ADR-023: Brand assets included and excluded

- Date: 2026-11-03. Status: Accepted (licensing assumption open).
- Decision: include the AuScope logo, reversed logo and icon (copied unmodified from
  PIDINST, renamed to kebab-case) and a 64×64 favicon derived from the icon. Exclude
  the Calibre fonts (commercial Klim typeface, no redistribution licence found; a
  system font stack is used instead), the NCRIS logos (footer, Issue #3) and the
  homepage hero photos (large content images with unknown credit).
- Assumption: AuScope has authorised use of its logos in this public package. Not yet
  confirmed; confirm with AuScope.
- CSS provenance: the CSS in `assets/css/` is newly written for this package. Only
  colour values and design conventions were taken from the reference
  `shared_style.css`; no rules were copied.
- Consequences: details and checksums are in
  `ckanext/auscope_core/public/auscope_core/ASSETS-LICENSES.md`; a test fails if an
  image has no entry there.

## ADR-024: Accessibility deviations from the legacy CSS

- Date: 2026-11-03. Status: Accepted.
- Decision:
  - Focus outlines are restored. `base.css` has one `:focus-visible` selector per
    CKAN 2.12.1 `outline: 0` rule on a rendered component (including
    `.page-header .nav-tabs li a`, `.navbar-toggler`, `.accordion-button`,
    `.btn-close`), at equal specificity.
  - Prose links are underlined (royal blue on body text is 1.24:1, WCAG 1.4.1). The
    selector is anchored on `.main` (rendered by `page.html` on every page) with
    `:is(p, dd, blockquote, td)` plus `.main .notes li a` and `.site-footer a`. Bare
    `li a` is excluded because facet, nav and action lists are standalone links.
  - The active-nav indicator is royal blue; teal (2.16:1 on white) is decorative only.
  - Danger, success, warning and info keep Bootstrap semantics; the legacy
    white-on-tangerine and white-on-red combinations are not reproduced.
  - Body font size is `1rem`, up from CKAN 2.12.1's `0.875rem`, for readability
    (close to the legacy `1.063rem`, without its forced-size selector list).
  - Dark-surface rule: containers with a primary or primary-hover background set
    `--auscope-focus-ring-color` and `--bs-heading-color` to explicit `var(...)`
    values, never `inherit` (which would give royal blue on royal blue).
- Consequences: `test_theme_css.py` checks token contrast (≥ 4.5 text, ≥ 3.0
  non-text) and these rules statically. Body text is 14 % larger on every CKAN page.

## ADR-025: `/auscope_core/` public namespace

- Date: 2026-11-03. Status: Accepted.
- Decision: shared static files live in `public/auscope_core/` and are served at
  `/auscope_core/...`, with kebab-case names (no spaces or en dashes).
- Consequences: no clash with consumers' existing `/base/images/AuScope Logo*.png`
  files while they migrate.

## ADR-026: Issue #2 branch base

- Date: 2026-11-03. Status: Accepted.
- Context: the Issue #1 and Issue #5 work is not on `origin/main`, which holds only
  the initial commit.
- Decision: `feature/2-shared-branding` is branched from
  `feature/5-ckan-compatibility` (`c2fd19c`).
- Consequences: merge in the order Issue #1 → #5 → #2, or rebase this branch onto
  `main` after those branches have merged.

---

## Verification record: Issue #2 (2026-11-03)

Environment: Windows host, Python 3.12.5, Podman 6.0.2; `ckan-dev` runs CKAN 2.12.1
on Python 3.14.10 (pytest 9.1.1). Browser: Microsoft Edge (headless, via Playwright
1.64.1 for Python with `channel="msedge"`).

| Check | Result |
|---|---|
| `ruff check .` (ruff 0.17.3) | `All checks passed!` |
| `pytest --ckan-ini=test.ini -p no:cacheprovider -v ckanext/auscope_core` | `56 passed` (7 in `test_plugin.py`, 14 in `test_theme.py`, 35 in `test_theme_css.py`) |
| Contrast test mutation: `--auscope-color-royal-blue: #59c2aa` | 9 failed (8 contrast pairs and the `-rgb` triplet test); reverted |
| Dark-surface test mutation: footer `--bs-heading-color: inherit` | the `.site-footer` dark-surface test failed; reverted |
| Favicon (Pillow 12.3.0 in `ckan-dev`) | `(64, 64) RGBA`; copied logos match the source MD5s |
| `pip wheel --no-deps` (clean `build/`) and listing | contains `webassets.yml`, the 4 CSS files, `js/auscope_core.js`, `templates/base.html`, the 4 PNGs and `ASSETS-LICENSES.md`; no `auscope_core.css` and no `.gitkeep` under `templates/` or `public/` (`i18n/.gitkeep` remains). No font files (excluded, ADR-023) |
| Wheel installed into a clean venv | entry point `ckanext.auscope_core.plugin:AuscopeCorePlugin`; CSS, PNGs, licence file and `templates/base.html` present in site-packages |
| Dev stack pages `/`, `/dataset`, `/dataset/auscope-branding-check`, `/user/login`, `/about` | all 200; all 20 same-origin CSS/JS/image URLs they reference return 200 (`/auscope_core/images/auscope-logo.png` and `auscope-favicon.png` as `image/png`) |
| Rendered `<head>` | `main.css` < `auscope_core-tokens.css` < `auscope_core.css`; logo `src` and favicon `href` point at `/auscope_core/images/` |
| `podman compose logs --since 30m ckan-dev` searched for `unknown asset`, `Traceback`, ` 404 `, ` 500 ` | no asset or page errors. 404s only from the seed script's expected `organization_show` / `package_show` existence checks. One `PermissionError` traceback from the image start script writing `/srv/app/src/ckan/test-core.ini` on container restart; not caused by this extension |
| Headless Edge, 1280×900 and 375×800, home, `/dataset` and the demo dataset (33 checks) | all passed: masthead background equals `--auscope-masthead-bg` (white); logo 48 px / 36 px tall; footer `rgb(40, 37, 114)` with white text; "Search data" and "Popular tags" white; homepage search input and popular-tag focus outlines white, submit button outline royal blue at −3 px offset; Dataset tab focus outline 3 px solid royal blue; 375 px toggler focus outline 3 px solid; notes links underlined; no horizontal overflow added by the theme. 0 console errors, 0 page errors, 0 responses ≥ 400 |
| Screenshots (viewed) | light masthead with teal line and AuScope logo, light grey surface, white readable headings on the blue homepage search box, blue footer with white text, collapsed toggler at 375 px, `/dataset` at 375 px wraps without clipping |
| Reference repositories | ckan-docker HEAD `2c10d5b0`, 8 porcelain entries; PIDINST HEAD `974efdfd`, 4 modified and 6 untracked: identical to the snapshot |

Demo dataset: created in the dev database by a scratch script run inside `ckan-dev`.
It creates a dev-only sysadmin with a random password, gets an API token inside the
container, and calls `organization_create` and `package_create`
(`auscope-branding-check`, notes with a Markdown paragraph link and a list-item
link). The token is never printed or stored in the repository.

Not verified: CKAN 2.11.4 and 2.10.1; browsers other than Edge (Chromium); a manual
keyboard and screen-reader walkthrough by a person; the menu toggler opened and nav
links tapped at 375 px; RTL rendering. CKAN 2.12.1 itself overflows a 375 px
viewport by 6 px (`.row` negative margins in the page and footer); this exists with
the AuScope stylesheets removed and is not changed by this issue.
