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

- Date: 2026-11-02. Status: Accepted.
- Context: Issue #1 is the skeleton only; styling, branding and UI are separate
  issues.
- Decision: implement only `IConfigurer`. No template overrides, helpers or
  blueprints. `templates/`, `public/` and `i18n/` contain `.gitkeep` only.
- Consequences: enabling the plugin does not change the UI. Empty directories are
  not packaged into a wheel (only editable installs have them). A non-editable
  install with these directories missing has not been tested; the issue goes away
  once the directories hold real files.

## ADR-008: Placeholder Webassets bundles

- Date: 2026-11-02. Status: Accepted.
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
