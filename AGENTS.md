# AGENTS.md

Canonical development instructions for people and AI coding agents (Kiro, Codex and
others) working on `ckanext-auscope-core`. The `.kiro/steering/` files and `docs/`
refer back to this file; if they disagree, this file wins.

## Project

`ckanext-auscope-core` is a standalone CKAN extension that provides shared branding,
themes, layouts, reusable UI components and common frontend functionality for four
AuScope repositories: the Data Repository, the Sample Repository, the Instrument
Registry (PIDINST) and the RAiD Repository. Its goals are easier maintenance, less
duplicated code and simpler CKAN upgrades. Python package `ckanext.auscope_core`,
CKAN plugin name `auscope_core`.

## CKAN compatibility policy

Maintain one extension codebase across the AuScope CKAN versions where practical.

| CKAN version | Role | Compatibility status |
|---|---|---|
| 2.12.1 | Primary development and release target | Verified only when the current test suite passes against this exact version |
| 2.11.4 | Secondary target for PIDINST | Targeted, but not yet verified |
| 2.10.1 | Legacy Data/Sample migration target | Evaluate during migration; not currently supported or verified |

- Use CKAN 2.12.1 supported APIs as the baseline, choosing APIs also present in the
  older targets when this does not compromise the primary target.
- Do not claim compatibility with a CKAN version until the extension's integration
  suite has passed against that exact version and the result is recorded.
- Prefer common CKAN APIs and templates over compatibility wrappers. Add a
  version-specific branch only for a demonstrated incompatibility covered by tests.
- Test the oldest Python version allowed by both this package and each CKAN target.
  The package currently requires Python 3.10 or newer, even where CKAN itself allows
  an older Python version.

## Reference repositories

The existing AuScope Data, Sample and PIDINST repositories are reference implementations. Inspect them to identify reusable components and established conventions. Do not modify these repositories. All implementation changes must be made within ckanext-auscope-core. Apply the compatibility policy above rather than copying legacy implementations.

| Repository | Local path | Notes |
|---|---|---|
| Data and Sample | `C:\MyFiles\040_Ckan\ckan-docker` | Extensions in `ckan/src/ckanext-auscope-theme` and `ckan/src/ckanext-igsn-theme` |
| Instrument Registry (PIDINST) | `C:\MyFiles\140-PIDINST\AuScope-instrument-registry` | |

Never copy credentials or `.env` values from these repositories.

## Permanent development rules

- Prefer native CKAN extension APIs over custom implementations.
- Never modify CKAN core.
- Minimise overrides of CKAN core templates.
- Keep repository navigation, authentication workflows, annual reporting links and
  homepage copy in consumer extensions; customise shared layouts through the
  documented CKAN and `auscope_*` blocks.
- Keep reusable snippets under `templates/snippets/auscope_core/` and their CSS
  under the `.auscope-core-*` namespace. Make them opt-in unless a global override
  is proven necessary; prefer CKAN's maintained dataset, resource, organisation,
  group, form and facet snippets.
- Keep business logic and repository-specific schemas out of the shared extension.
- Use maintainable Python code with clear tests.
- Pin dependencies where appropriate.
- Follow existing established conventions.
- Keep documentation concise and accurate.
- Update relevant project documentation whenever implementation changes affect
  architecture, configuration, dependencies or developer workflows.
- Record important technical decisions and their rationale.
- Do not invent successful test results or claim compatibility without verification.

## Styling rules

- Brand values (colours, fonts, sizes) live only in
  `ckanext/auscope_core/assets/css/tokens.css` as `--auscope-*` tokens. Other CSS
  files only reference tokens. Product-specific styles stay in consumer extensions.
- Dark-surface rule: any container given a primary or primary-hover background must
  also set `--auscope-focus-ring-color` and `--bs-heading-color` explicitly to the
  on-primary (or footer) colour, for example
  `--auscope-focus-ring-color: var(--auscope-color-on-primary)` and
  `--bs-heading-color: var(--auscope-color-on-primary)`. Do not use `inherit`: on a
  custom property it inherits the parent's value of that property, which is royal
  blue.
- Never remove focus outlines. When CKAN adds an `outline: 0` rule for a rendered
  component, add a matching `:focus-visible` selector (same specificity) to the
  focus list in `base.css`.
- Keep the `TEXT_PAIRS` / `NON_TEXT_PAIRS` contrast tests passing; teal is decorative
  only, never text or the only state indicator.
- Every new brand asset needs an entry in
  `ckanext/auscope_core/public/auscope_core/ASSETS-LICENSES.md`. Do not ship fonts
  or images without a known redistribution licence.
- Keep the shared CSS free of `url()` references and of `!important` (except in the
  reduced-motion block).

## Working rules

- Work on a feature branch named `feature/<issue-number>-<short-slug>`, one GitHub
  issue per branch.
- Do not push, merge, open releases or publish packages without explicit user
  approval.
- Never commit `.env`, credentials or other secrets. `.env.example` holds
  placeholders only.
- Keep automated tests pointed at the dedicated `solr-test` service. Never run CKAN
  test fixtures against the development `solr` service or its volume.
- Tests must use the `ckan_test` database, never `ckan_default`. In Compose, run
  every test and test-DB command through `sh docker/ckan/test-env.sh`, because the
  container's `CKAN_*` connection variables override `test.ini`.
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
| Init test DB | `docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev sh docker/ckan/test-env.sh ckan -c test.ini db init` |
| Run tests | `docker compose exec -w /srv/app/src_extensions/ckanext-auscope-core ckan-dev sh docker/ckan/test-env.sh pytest --ckan-ini=test.ini -v ckanext/auscope_core` |
| Check plugin loaded | `GET http://localhost:5000/api/3/action/status_show` lists `auscope_core` |
| Stop dev stack | `docker compose down` |

## Where things live

| Topic | File |
|---|---|
| Installation, development and testing | `README.md` |
| Architecture and extension design | `docs/architecture.md` |
| Decisions, rationale and verification records | `docs/decisions.md` |
| Kiro steering (product, tech, structure) | `.kiro/steering/*.md` |
| Theme tokens (customisation API) | `ckanext/auscope_core/assets/css/tokens.css` |
| Styling architecture and load order | `docs/architecture.md` ("Styling architecture") |
| Theme customisation and visual check | `README.md` ("Theme and branding") |
| Shared template customisation | `README.md` ("Shared templates and layouts") |
| Reusable UI analysis and exclusions | `docs/ui-component-analysis.md` |
| Extension inventory and compatibility management | `docs/extension-compatibility.md` |
| Asset licences and attribution | `ckanext/auscope_core/public/auscope_core/ASSETS-LICENSES.md` |
| Reference-repository branding analysis | `docs/branding-analysis.md` |
| Shared visual baseline and legacy differences | `docs/design-baseline.md` |

## Definition of done

- Tests were run and the real results are reported, including anything that could
  not be verified.
- `ruff check .` passes.
- README, `docs/` and this file are updated when architecture, configuration,
  dependencies or developer workflows change.
- Significant decisions are recorded in `docs/decisions.md`.
