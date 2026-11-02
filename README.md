# ckanext-auscope-core
Shared CKAN extension providing AuScope branding, themes, reusable UI components and common functionality to simplify maintenance and CKAN upgrades across AuScope repositories.

## Status

Extension skeleton ([Issue #1](https://github.com/AuScope/ckanext-auscope-core/issues/1)).
The plugin loads and registers its template, public and Webassets directories, but
does not change the CKAN UI yet. Shared styling, branding and UI components are
tracked in separate issues.

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

The extension has no configuration options yet.

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
docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev ckan -c test.ini db init
docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev pytest --ckan-ini=test.ini -v ckanext/auscope_core
```

Tests use CKAN core's pytest plugin and fixtures. `test.ini` inherits
`../../src/ckan/test-core.ini`, which resolves inside the `ckan-dev` container. For a
CKAN source install, change the `use = config:` line to point at your CKAN source's
`test-core.ini` and set `solr_url` to a test-only Solr core. In Compose, both
`test.ini` and `TEST_CKAN_SOLR_URL` point at the dedicated `solr-test` service; do
not point either at the development `solr` service.

## Linting

```bash
pip install -r dev-requirements.txt
ruff check .
```

## Project structure

```
ckanext-auscope-core/
├── AGENTS.md                    # AI development instructions (canonical rules)
├── docs/                        # architecture.md, decisions.md (ADR log)
├── .kiro/steering/              # Kiro steering files (point to AGENTS.md and docs/)
├── .github/workflows/test.yml   # CI: tests in ckan/ckan-dev:2.12.1, ruff lint
├── docker-compose.yml           # Development stack: CKAN, PostgreSQL, Solr, Redis
├── docker/
│   ├── ckan/Dockerfile.dev      # ckan-dev image with the extension installed editable
│   └── postgres/initdb/         # Creates the CKAN role and dev/test databases
├── .env.example                 # Template for the local .env (never commit .env)
├── pyproject.toml               # Package metadata, ckan.plugins entry point, tool config
├── setup.cfg, setup.py          # Setuptools/Babel settings (CKAN cookiecutter layout)
├── requirements.txt             # Runtime dependencies (none beyond CKAN)
├── dev-requirements.txt         # Development tools (ruff)
├── test.ini                     # pytest configuration inheriting CKAN's test-core.ini
└── ckanext/
    └── auscope_core/
        ├── plugin.py            # AuscopeCorePlugin (IConfigurer)
        ├── templates/           # Shared Jinja templates (empty for now)
        ├── public/              # Static files served as-is (empty for now)
        ├── assets/              # Webassets library "auscope_core" (webassets.yml)
        ├── i18n/                # Translations (empty for now)
        └── tests/               # pytest tests
```

## Documentation

- [AGENTS.md](AGENTS.md): development rules for people and AI agents
- [docs/architecture.md](docs/architecture.md): extension design
- [docs/decisions.md](docs/decisions.md): technical decisions and verification records
