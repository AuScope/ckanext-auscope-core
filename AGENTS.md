# AGENTS.md

Canonical development instructions for people and AI coding agents (Kiro, Codex and
others) working on `ckanext-auscope-core`. The `.kiro/steering/` files and `docs/`
refer back to this file; if they disagree, this file wins.

## Project

`ckanext-auscope-core` is a standalone CKAN 2.12.1 extension that provides shared
branding, themes, layouts, reusable UI components and common frontend functionality
for four AuScope repositories: the Data Repository, the Sample Repository, the
Instrument Registry (PIDINST) and the RAiD Repository. Its goals are easier
maintenance, less duplicated code and simpler CKAN upgrades. Python package
`ckanext.auscope_core`, CKAN plugin name `auscope_core`.

## Reference repositories

The existing AuScope Data, Sample and PIDINST repositories are reference implementations. Inspect them to identify reusable components and established conventions. Do not modify these repositories. All implementation changes must be made within ckanext-auscope-core. Prefer CKAN 2.12.1 supported APIs and conventions over copying legacy implementations.

| Repository | Local path | Notes |
|---|---|---|
| Data and Sample | `C:\MyFiles\040_Ckan\ckan-docker` | Extensions in `ckan/src/ckanext-auscope-theme` and `ckan/src/ckanext-igsn-theme` |
| Instrument Registry (PIDINST) | `C:\MyFiles\140-PIDINST\AuScope-instrument-registry` | |

Never copy credentials or `.env` values from these repositories.

## Permanent development rules

- Prefer native CKAN extension APIs over custom implementations.
- Never modify CKAN core.
- Minimise overrides of CKAN core templates.
- Keep business logic and repository-specific schemas out of the shared extension.
- Use maintainable Python code with clear tests.
- Pin dependencies where appropriate.
- Follow existing established conventions.
- Keep documentation concise and accurate.
- Update relevant project documentation whenever implementation changes affect
  architecture, configuration, dependencies or developer workflows.
- Record important technical decisions and their rationale.
- Do not invent successful test results or claim compatibility without verification.

## Working rules

- Work on a feature branch named `feature/<issue-number>-<short-slug>`, one GitHub
  issue per branch.
- Do not push, merge, open releases or publish packages without explicit user
  approval.
- Never commit `.env`, credentials or other secrets. `.env.example` holds
  placeholders only.
- Work autonomously. Ask only when blocked by missing credentials, an irreversible or
  high-risk action, or an architectural decision with significant consequences.
- Record assumptions and decisions in `docs/decisions.md`.

## Commands

Run from the repository root. See README.md for details.

| Task | Command |
|---|---|
| Lint | `ruff check .` (version pinned in `dev-requirements.txt`) |
| Build wheel | `pip wheel --no-deps -w dist .` |
| Start dev stack | `cp .env.example .env` then `docker compose up -d --build` (or `podman compose`) |
| Init test DB | `docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev ckan -c test.ini db init` |
| Run tests | `docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev pytest --ckan-ini=test.ini -v ckanext/auscope_core` |
| Check plugin loaded | `GET http://localhost:5000/api/3/action/status_show` lists `auscope_core` |
| Stop dev stack | `docker compose down` |

## Where things live

| Topic | File |
|---|---|
| Installation, development and testing | `README.md` |
| Architecture and extension design | `docs/architecture.md` |
| Decisions, rationale and verification records | `docs/decisions.md` |
| Kiro steering (product, tech, structure) | `.kiro/steering/*.md` |

## Definition of done

- Tests were run and the real results are reported, including anything that could
  not be verified.
- `ruff check .` passes.
- README, `docs/` and this file are updated when architecture, configuration,
  dependencies or developer workflows change.
- Significant decisions are recorded in `docs/decisions.md`.
