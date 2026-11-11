# Extension compatibility and shared management

This document records the Issue #5 reference-repository inventory and the proposed
extension-management boundary. It is an analysis, not a migration plan: no reference
repository, extension version, schema or deployment configuration was changed.

## Scope and evidence

The inventory was taken on 2026-11-10 from these local, read-only snapshots:

| Repository | Snapshot | State relevant to the inventory |
|---|---|---|
| Data and Sample (`ckan-docker`) | `2c10d5b` on `dev-sample` | CKAN 2.10.1; branch was 87 commits behind its remote and already had 8 worktree entries |
| PIDINST (`AuScope-instrument-registry`) | `974efdf` on `master` | CKAN 2.11.4; branch was 7 commits behind its remote and already had 10 worktree entries |
| Core | `f8cff21` from `origin/main` | CKAN 2.12.1 development and CI baseline |

The Dockerfiles, safe configuration keys, plugin lists, startup scripts, package
metadata and Scheming YAML were inspected. Secret values were not read or copied.
The reference worktrees were not modified. Because the reference branches are behind
their remotes and most Dockerfile installs use floating branches, this is a build
declaration inventory, not proof of the exact packages in a running production image.
A production image's `pip freeze`, image digest and rendered CKAN configuration are
still needed before a migration.

## Compatibility status

"Verified" means the current Core integration suite passed against the exact CKAN
version. It does not extend to a consumer repository or optional extension merely
because that repository installs Core.

| CKAN / integration profile | Status | Evidence and limitation |
|---|---|---|
| Core on CKAN 2.12.1 | **Verified** | The complete isolated suite passes on the exact `ckan/ckan-dev:2.12.1` image; packaging, template inheritance, asset loading and reusable components are covered. |
| Core on CKAN 2.11.4 | **Unverified secondary target** | No full integration-suite result exists for this exact version. |
| Core on CKAN 2.10.1 | **Unverified legacy migration target** | Not currently supported or verified; evaluate during Data/Sample migration. |
| Data, Sample or PIDINST consumer stack on CKAN 2.12.1 | **Unverified** | Their schemas, consumer code, AuScope forks and optional extension combinations have not run together on 2.12.1. |
| Any consumer stack on its current CKAN version | **Not verified by Core CI** | The reference inventory records configuration only; it is not a consumer test result. |

## Repository comparison

| Concern | Data | Sample | PIDINST | Shared conclusion |
|---|---|---|---|---|
| CKAN | 2.10.1 | 2.10.1 | 2.11.4 | Core targets 2.12.1; older targets remain unverified |
| Consumer extension | `auscope_theme` 0.0.1 | `igsn_theme` 0.0.1 | `pidinst_theme` 0.0.1 | Keep consumer-owned; each contains domain logic as well as presentation |
| Authentication | local `oidc_pkce` 0.3.1 | same | same | Shared deployment capability, but not a Core dependency |
| Scheming plugins | datasets | datasets, organizations | datasets, organizations, groups in production | Enable only the Scheming forms each repository uses |
| Dataset schema | `dataset` Data schema | `dataset` Sample/IGSN schema | `instrument` PIDINST schema | Repository-owned contracts; do not move into Core |
| Organization schema | CKAN default | Sample organization schema | Instrument organization schema | Sample/PIDINST fields match, but labels, requiredness and meaning differ |
| Group schema | CKAN default | CKAN default | `party` schema | PIDINST-only domain model |
| Composite/repeating | composite fields in schema; common presets configured | same | same, with PIDINST-specific relations | Optional Scheming capability, not Core functionality |
| Spatial | `spatial_metadata spatial_query`; multi-point dataset geometry | same; includes sample point geometry | same; instrument/platform location | Common extension family, repository-specific schema semantics |
| DOI | AuScope DOI branch and repository policy | AuScope DOI branch plus theme metadata patch | PIDINST DOI branch and `IDoi` policy | Optional capability; policy and credentials stay in consumers |
| DCAT | enabled in inspected Data config | enabled in inspected Sample config | enabled | Optional publishing profile; AuScope fork must be verified on 2.12.1 |
| Contact | enabled; recipient/subject/Recaptcha/SMTP configuration | same key set | same key set | Package/version may be coordinated; values remain per deployment |
| Taxonomy | no | no | production only | PIDINST-only until another consumer demonstrates the need |
| Resource views | `image_view text_view recline_view` | same | `image_view text_view resource_proxy` | `recline_view` was removed in CKAN 2.12; migration must select maintained views |
| DataStore loader | `datastore datapusher` | same | same | Deployment infrastructure, outside Core |
| S3 filestore | installed, not present in inspected plugin lists | same | installed, not present in inspected plugin lists | Reconcile install-versus-activation before upgrade; do not make mandatory |
| ISO 19115 / zip preview | installed, not present in inspected plugin lists | same | installed, not present in inspected plugin lists | Treat as optional and verify whether they are actually used |

The Data and Sample plugin lists come from different environment files in the same
repository: `.env.dev` selects Data and `.env`/`.env.local` select Sample. PIDINST's
production `.env` additionally enables `scheming_groups`, `resource_proxy` and
`taxonomy`; its development/local lists do not consistently match production.

### Enabled plugin profiles

The meaningful non-core portions of the inspected profiles are:

| Profile | Enabled plugins |
|---|---|
| Data | `oidc_pkce auscope_theme contact scheming_datasets composite spatial_metadata spatial_query doi dcat dcat_json_interface structured_data` |
| Sample | `oidc_pkce igsn_theme contact scheming_datasets scheming_organizations composite spatial_metadata spatial_query doi dcat dcat_json_interface structured_data` |
| PIDINST production | `oidc_pkce pidinst_theme contact scheming_datasets scheming_organizations scheming_groups composite spatial_metadata spatial_query doi dcat dcat_json_interface structured_data taxonomy` |

Native view, DataStore/loader and environment plugins are omitted from this compact
table. The complete inspected strings also contain those plugins and are recorded in
the reference environment files. They should be regenerated from a declarative
profile rather than copied by hand during migration.

## Installed extension sources and reproducibility

| Extension | Data / Sample declaration | PIDINST declaration | Pin and 2.12.1 consideration |
|---|---|---|---|
| `ckanext-spatial` | upstream default branch | upstream default branch | Unpinned. Upstream v2.3.2 records CKAN 2.12 support; test the selected release with Solr 9 and the AuScope schemas. |
| `ckanext-doi` | AuScope `auscope_customise` | AuScope `auscope_pidinst` in production; `ckan-2.11` in dev | Floating, inconsistent branches. Direct metadata monkey-patching and PIDINST `IDoi` integration need consumer tests. |
| `ckanext-iso19115` | AuScope `auscope_data_repo_customise` | same | Floating optional fork; activation/use is unclear. |
| `ckanext-contact` | PyPI, no version | same | Unpinned; test forms, mail and Recaptcha against CKAN 2.12.1. |
| `ckanext-s3filestore` | upstream default branch | AuScope `ckan-2.11` in production; upstream default in dev | Floating and inconsistent; CKAN 2.12's filestore changes make this a separate migration workstream. |
| `ckanext-scheming` | upstream `master` | same | Unpinned. Upstream declares CKAN 2.10+ and its 2.12 CI work is complete. |
| `ckanext-repeating` | upstream default branch | same | Unpinned; presets are configured although no plugin is enabled. Verify compatibility with the selected Scheming revision. |
| `ckanext-composite` | EnviDat default branch | same | Unpinned; schema and templates depend on its presets/validators. Verify jointly with Scheming/repeating. |
| `ckanext-zippreview` | AuScope `master` | same | Unpinned and apparently inactive in inspected profiles. |
| `ckanext-dcat` | requirements from upstream `master`, then AuScope `auscope_customise` | same | Two floating sources. Upstream 2.12 CI work is complete, but the AuScope fork remains unverified. |
| `ckanext-taxonomy` | not installed | AuScope `master` | Unpinned PIDINST-only dependency with database initialization and seed data. |
| `ckanext-oidc-pkce` | local 0.3.1 | local 0.3.1 | Versioned locally but not locked to a source commit in the image build. |

Only the spatial helper requirements contain meaningful pins: Data/Sample pin
OWSLib 0.28.1, geojson 3.0.1 and a pyproj commit for Python 3.9+, while PIDINST uses
newer lower/compatible ranges. These hand-maintained files must not be copied into a
2.12 build; select a supported spatial release and resolve one constraints set with
CKAN 2.12.1's own requirements.

## Schema comparison

Data and Sample share 30 distinct top-level field names (31 schema entries because
`name` occurs at dataset and resource level), including authors, resource type,
keywords, GCMD and Fields of Research terms, location/EPSG fields, funding, related
resources, publisher, credit, citation, owner and resource fields. Their shared
names do not imply identical contracts: labels, requiredness, snippets, validators
and DOI meaning differ.

Data-only fields include the deposit declaration, deposit/embargo and temporal
coverage dates, lineage, licence and primary contact. Sample-only fields include
sample identifiers and parentage, sample type, point geometry, acquisition dates,
method, depth, commodities and repository contact. PIDINST uses an `instrument`
type with identifier-source and DOI lifecycle, instrument/platform classifications,
party-backed owner/manufacturer/funder composites, measured variables, relations,
publication/withdrawal state and instrument resources.

The Sample and PIDINST organization schemas have the same six field names (`title`,
`name`, `contact_name`, `contact_email`, `description`,
`is_culturally_sensitive`) but differ in wording and requiredness. PIDINST alone has
the `party` group type and its ROR, role, state and hierarchy fields. Core should not
own any of these schemas. Duplication may be reduced later through reviewed
consumer-side generation or a schema library only if Scheming gains a composition
mechanism that preserves each repository's validation and migration history.

## Plugin order and dependency findings

Plugin order is part of the compatibility contract, not a cosmetic setting:

- a consumer theme must be listed before `auscope_core`, so its template directory
  takes precedence and `{% ckan_extends %}` reaches the shared template;
- PIDINST's plugin code explicitly requires `doi` before `pidinst_theme` for its
  `after_dataset_update` observation, but the inspected production list has
  `pidinst_theme` before `doi`; correct and regression-test this in the PIDINST
  migration, not in Core;
- Scheming dataset/organization/group plugins and the presets required by a schema
  must be present before exercising consumer forms;
- only activate `taxonomy`, group Scheming, DCAT interfaces, spatial query, contact,
  DOI and storage plugins in profiles that use them; and
- retain `envvars` in the position required by its selected release. The inspected
  deployments put it first while Core's current deployment guidance puts it last,
  so this must be resolved from the pinned release's documentation and an effective
  configuration test.

An illustrative PIDINST capability order is therefore native CKAN plugins, Scheming
and its field extensions, spatial/DCAT/contact as required, `doi`, `taxonomy`,
`pidinst_theme`, `auscope_core`, then the verified position for `envvars`. The final
order must be owned and tested by the PIDINST deployment rather than hard-coded by
Core.

## Recommended architecture

### Keep in `ckanext-auscope-core`

- shared AuScope design tokens, assets, accessible base styling and focused layout
  overrides;
- namespaced, opt-in UI snippets with no product policy;
- the documented consumer blocks and template/asset compatibility tests; and
- a compatibility manifest/report of combinations that have actually passed.

Core should keep an empty runtime dependency list beyond CKAN. Installing Core must
not install Scheming, contact, spatial, DOI, DCAT, taxonomy, authentication, storage
or a loader.

### Manage centrally without making mandatory

Maintain one reviewed constraints/lock input in deployment tooling for the exact
commits or releases of commonly selected extensions: Scheming, repeating,
composite, spatial, contact, DOI and DCAT, plus their transitive constraints. A
central manifest should record source URL, immutable tag/commit, compatible CKAN
and Python versions, enabled plugin names, migrations and the consumer suites that
passed. It should define capability groups, not one universal installation:

- `metadata-forms`: Scheming plus only the field extensions a schema uses;
- `geospatial`: spatial metadata/query and supported binary/system dependencies;
- `publication`: DOI and/or DCAT;
- `contact`: contact plus mail/Recaptcha configuration;
- `pidinst-taxonomy`: taxonomy and seed/migration steps; and
- repository-selected authentication, storage, preview and loading capabilities.

The lock belongs in deployment/build tooling (or a dedicated integration project),
not `ckanext-auscope-core`'s `install_requires`. Core can link to the tested manifest
without coupling a theme release to unrelated database extensions.

Pins must be immutable: prefer a released artifact with a version and verified
hash, or a full Git commit SHA when an AuScope fork has no suitable release. Do not
use `master`, another moving branch name or an unbounded PyPI requirement. Resolve
each capability group against CKAN 2.12.1's constraints, retain the resulting lock
and image digest, and update a pin only through a tested compatibility change.

### Keep repository-specific

- all dataset, organization and group Scheming YAML;
- custom validators, actions, auth, facets and form/display snippets;
- DOI prefixes, credentials, minting/withdrawal policy and metadata mappings;
- taxonomy vocabularies and party/instrument propagation;
- spatial field semantics, repository navigation, OIDC configuration, contact
  recipients, annual-reporting links and homepage copy; and
- activation of optional plugins and repository database migrations.

## CKAN 2.12.1 compatibility risks

- CKAN 2.12 requires Python 3.10+, a requirements upgrade, database upgrade and
  DataStore permission/upgrade work. Its group/organization extras and package
  indexing changes require consumer logic tests.
- Recline view plugins were removed. Data and Sample must replace `recline_view`
  and review `ckan.views.default_views` before migration.
- CKAN 2.12 introduces new file storage APIs. Existing S3 filestore usage must be
  established and migrated separately; an installed-but-disabled package is not
  evidence of compatibility.
- Upstream Scheming, DCAT and spatial projects completed CKAN 2.12 CI work, but
  AuScope forks and the contact/composite/repeating/taxonomy/DOI combination have
  not been verified on 2.12.1.
- Consumer extensions import DOI internals, monkey-patch metadata generation and
  implement broad CKAN interfaces. These are higher-risk than Core's public
  `IConfigurer` surface and need end-to-end tests with real schemas.
- Core itself requires Python 3.10+, so it cannot be installed into older Python
  environments even when CKAN 2.10/2.11 would otherwise allow them.

## Deferred consumer migration tasks

These findings are deliberately not Core changes:

- **PIDINST plugin order:** move `doi` before `pidinst_theme` in the future PIDINST
  integration profile and add a regression test for the DOI publication hook before
  changing its deployment.
- **Data/Sample resource views:** replace the removed `recline_view` with a
  CKAN-2.12-supported view and review `ckan.views.default_views` during each
  consumer migration.

Both tasks require consumer-owned testing and separate approval. This issue does
not modify their plugin lists, schemas, dependencies or migrations.

## Safe compatibility workflow

1. Capture each production image digest, `pip freeze`, effective plugin order and
   non-secret configuration keys. Compare them with this source inventory.
2. Choose immutable extension tags/commits in a proposed central constraints file;
   do not update production Dockerfiles yet.
3. Build disposable CKAN 2.12.1 integration images per capability profile. Use a
   fresh `ckan_test` database, dedicated Solr core/service and isolated Redis DB.
4. Run Core's isolated suite first, then consumer contract tests for plugin load,
   schema validation, create/update/show/search, templates/assets, DOI/DCAT output,
   spatial search, contact forms and taxonomy where applicable.
5. Restore anonymized database and filestore copies into an isolated rehearsal,
   run documented CKAN and extension migrations, and compare record/resource counts
   and representative API output. Never point fixtures at development or production
   services.
6. Record the exact passing image/commit matrix. Only then claim compatibility or
   propose a repository migration for approval.

## Current Core CI coverage

The existing workflow already runs the installed package and complete pytest suite
on the exact `ckan/ckan-dev:2.12.1` image, with PostgreSQL, Redis and CKAN 2.12 Solr.
It verifies a non-editable package install, plugin registration, template/public
paths, Webassets registration and serving, stylesheet order, images, common page
rendering, inheritance/customisation blocks and reusable components. Ruff runs as a
separate required job. This satisfies the Core-only Issue #5 test and CI scope.

| Issue #5 acceptance criterion | Existing CI evidence | Result |
|---|---|---|
| Automated tests run successfully | The workflow initializes `ckan_test` and runs the installed package's complete pytest suite. | Covered |
| CI is configured | `.github/workflows/test.yml` runs test and Ruff jobs on pushes and pull requests. | Covered |
| CKAN 2.12.1 compatibility is verified | The test job uses the exact `ckan/ckan-dev:2.12.1` image and matching CKAN 2.12 Solr/PostgreSQL services. | Covered for Core only |
| Template inheritance, assets and reusable components | Tests render common pages, inspect consumer blocks, register and fetch Webassets/static files, verify stylesheet order and exercise namespaced components. | Covered |
| Supported versions and limitations are documented | This status matrix and `docs/architecture.md` distinguish verified, targeted and unverified combinations. | Covered |

It does not prove any consumer or optional extension combination. The next CI layer
should live with the consumer or integration profiles and call the same Core suite;
adding every optional extension to Core's unit-test image would incorrectly make
them mandatory and would hide repository-specific migration failures.

## Sources

- [CKAN 2.12.1 changelog](https://docs.ckan.org/en/2.12/changelog.html)
- [CKAN extension 2.12 support tracker](https://github.com/ckan/ckan/issues/9364)
- [ckanext-scheming requirements](https://github.com/ckan/ckanext-scheming)
- [ckanext-spatial releases](https://github.com/ckan/ckanext-spatial/releases)
- [ckanext-dcat](https://github.com/ckan/ckanext-dcat)
