# Shared vocabulary, taxonomy, Party and geographic functionality review

- Status: technical assessment and implementation plan only
- Reviewed: 17 November 2026

## Executive summary

PIDINST contains the most complete implementations, but much of its sophistication
is specific to the Instrument Registry's metadata and lifecycle. Core should not
absorb PIDINST's taxonomy database, Party registry, instrument roles, propagation
jobs or spatial indexing policy.

The recommended boundary is:

- add provider-neutral vocabulary search services, external-provider adapters and
  opt-in picker components to AuScope Core;
- add small, pure, namespaced geographic validation utilities to Core, while each
  consumer retains its schema policy and spatial-index transformation;
- continue to use `ckanext-taxonomy` for taxonomy persistence, hierarchy, actions,
  administration and import, with PIDINST retaining its instrument-specific
  protection and propagation customisations;
- retain Party management in PIDINST for now, but make the ROR lookup client and a
  provider-neutral organisation picker reusable through Core; and
- do not create another extension yet. A separate Party extension is justified only
  if a second repository adopts the same Party domain and lifecycle.

The first implementation task should be the shared geographic validation
primitives. Latitude, longitude and bounding-box validation are already copied
almost verbatim across all three implementations, have no external-service
dependency and can be extracted without changing any schema or stored value.

## Scope and evidence

The review inspected these working trees without modifying them:

| Repository | Revision reviewed | Primary locations |
|---|---|---|
| AuScope Core | `6d43ba16909b` | `ckanext/auscope_core`, `docs/` |
| PIDINST | `974efdfd25c7` | `ckan/src/ckanext-pidinst-theme/ckanext/pidinst_theme` |
| Data and Sample | `2c10d5b0cb1e` | `ckan/src/ckanext-auscope-theme`, `ckan/src/ckanext-igsn-theme`, `ckan/src/shared` |
| AuScope `ckanext-taxonomy` | `776bd1df26a062da71e7a7205e846fedbe49f1de` | models, actions, auth, views, CLI and tests |

The reference repositories had pre-existing working-tree changes. They were used
read-only. No service was started and no integration test was run, so this review
does not establish compatibility with CKAN 2.12.1, 2.11.4 or 2.10.1. Compatibility
statements below distinguish source-level assessment from verified support.

## Current implementation map

| Concern | PIDINST | Data/Sample | Appropriate owner |
|---|---|---|---|
| FOR lookup | Proxy and picker assets exist, but the current instrument schema does not use them | Active split code/label fields | Core provider and picker; consumer schema mapping |
| EPSG lookup | Proxy route and map UI | Near-identical proxy and map UI | Core provider; consumer CRS policy |
| GCMD lookup | Search, narrower-term lookup, tree and combined pickers | Search and split code/label fields | Core provider; consumer-selected schemes and storage mapping |
| ROR lookup | ROR v2 search plus hierarchy and Party creation | Older direct browser lookup | Core lookup only; PIDINST Party lifecycle |
| Custom taxonomy | `ckanext-taxonomy` plus PIDINST protections and propagation | Not active | Third-party extension plus consumer integration |
| Party registry | CKAN group type with instrument roles and snapshot propagation | Simple organisation/affiliation use | PIDINST until a second shared use case exists |
| Geographic validation | Point/area validator and first-feature spatial conversion | Similar copied validators; Sample adds elevation | Core primitives; consumer schema and indexing adapter |

## 1. Vocabulary services

### Backend providers and endpoints

PIDINST registers proxy endpoints in `ckanext/pidinst_theme/views.py`.

| Provider | Current behaviour | Main concerns |
|---|---|---|
| FOR | Queries the ARDC ANZSRC 2020 Fields of Research LDA endpoint with label search and paging | No request timeout, exception handling, input bounds or server cache |
| EPSG | Queries `apps.epsg.org/api/v1/CoordRefSystem` with keyword search and paging | No request timeout, exception handling, input bounds or server cache |
| GCMD | Allowlisted scheme search through ARDC LDA; can merge a domain scheme with Science Keywords and deduplicate by URI or label | Dated vocabulary paths are hard-coded; only per-request merging; no server cache |
| GCMD narrower terms | Resolves a resource, then performs sequential child lookups | N+1 upstream calls, mixed 8/15 second timeouts and partial-result behaviour |
| ROR | Queries ROR v2, applies owner/manufacturer policy filters and resolves parent organisations | Policy is mixed into transport; sequential hierarchy calls; no cache; direct ROR URL lookup is constructed incorrectly |
| Local field terms | Searches up to 1,000 instrument packages and derives suggestions from selected fields | Repository-specific, incomplete pagination and not an external vocabulary service |
| Taxonomy terms | Calls `taxonomy_term_list`, filters locally and returns at most 100 matches | The endpoint contains recursive flattening although the called action returns a flat list; availability is coupled to the optional plugin |

The Data and Sample themes contain near-identical unnamespaced `/api/proxy`
implementations for FOR, EPSG and GCMD. Registering the same aliases in Core would
therefore create route ownership ambiguity during incremental adoption.

The stronger PIDINST GCMD and ROR routes use allowlists and explicit timeouts and
map failures to HTTP responses. FOR and EPSG still issue bare `requests.get` calls.
None of the external-provider routes has a bounded server-side cache, retry policy,
rate-limit handling or stale-result strategy. Select2's `cache: true` is only a
browser-side option and is not a substitute for service caching.

### Search, autocomplete and stored values

The principal PIDINST JavaScript modules are:

- `assets/js/for-fields-handler-module.js`, which searches after three characters
  and stores comma-separated identifiers plus a hidden JSON label representation;
- `assets/js/gcmd-fields-handler-module.js`, which stores GCMD identifiers/URIs and
  hidden labels;
- `assets/js/vocab-picker-module.js`, which combines GCMD and custom-taxonomy
  results and supports composite or split storage modes;
- `assets/js/gcmd-taxonomy-tree-module.js`, which renders lazy GCMD trees and calls
  the narrower-term endpoint; and
- `assets/js/field-terms-autocomplete-module.js`, which learns suggestions from
  existing instrument packages.

The corresponding templates are under
`templates/scheming/form_snippets/` and
`templates/snippets/pidinst_theme/`. PIDINST's active instrument schema uses the
combined vocabulary/taxonomy picker for instrument types and measured variables.
FOR assets are present but are not used by the current instrument schema. Data and
Sample actively use split identifier and display-label fields for FOR and GCMD.

This establishes a useful compatibility rule: an extraction must preserve each
consumer's submitted field names and exact stored representation. A common picker
can normalise search results, but the mapping to split fields, composite subfields
or plain scalar fields belongs to the consumer.

### Schema integration and validation

Current schemas largely trust values returned by the browser. They do not
revalidate an identifier against ARDC, EPSG or ROR on package create/update. That
is preferable to making writes depend on provider availability, but the backend
should still validate the local contract: allowed provider, identifier syntax,
string length, cardinality and field shape.

Stable external identifiers should remain the canonical stored value, with labels
treated as display snapshots. Provider lookup must not be required to read or edit
an existing record. This is especially important for versioned GCMD sources and
renamed ROR organisations.

### Reusable and consumer-specific parts

Reusable through Core:

- provider transport, response normalisation and consistent error responses;
- search and hierarchy contracts such as `{id, label, source, metadata}`;
- input limits, allowlists, configured timeouts and bounded stale-tolerant caches;
- an opt-in autocomplete/tree component with configurable endpoints and submitted
  field mappings; and
- mocked provider-contract tests and provider health diagnostics.

Consumer-owned:

- which vocabularies and versions are permitted;
- requiredness, role filtering and repository-specific ranking;
- split versus composite field storage;
- learned terms from local datasets; and
- instrument-specific merging of GCMD and local taxonomy concepts.

## 2. Custom taxonomy

### What `ckanext-taxonomy` already provides

The AuScope fork reviewed is version 1.1.0, requires Python 3.8 or newer and has
runtime dependencies on RDFLib and PyYAML. It provides:

- `taxonomy` and `taxonomy_term` tables with UUID primary keys;
- a self-referencing `parent_id` relationship and hierarchical children;
- taxonomy and term list, show, create, update and delete actions;
- a separate nested `taxonomy_term_tree` action;
- Flask administration views for taxonomy and term CRUD;
- SKOS import and YAML default seeding through the CLI; and
- mutation auth for sysadmins or admins of configured organisations.

PIDINST installs this extension separately, activates its plugin only in the
PIDINST profile and seeds instrument, platform and measured-variable taxonomies at
container startup. Its form picker stores a taxonomy term URI or label alongside a
display name in composite fields.

### PIDINST customisations

PIDINST appropriately keeps repository-specific behaviour outside the taxonomy
extension:

- configured logical names and an allowlist of exposed taxonomies;
- custom taxonomy index, term detail and delete-confirmation templates;
- chained taxonomy update/delete actions;
- guards that prevent deleting terms still referenced by instruments, including
  referenced descendants; and
- label/URI propagation into instrument composite values when a term changes.

The propagation scans instrument packages and patches matching values. It runs in
in-process daemon threads with a local task-status table. This can lose work when a
web worker restarts and needs explicit multi-worker and database-session testing.
It is instrument lifecycle logic, not generic taxonomy functionality.

### Gaps to resolve in the taxonomy dependency

The source review identified issues that should be addressed in the taxonomy
extension or its maintained AuScope fork rather than copied into Core:

- the documented container test command covers loader, view and CLI tests, but not
  a full CKAN action/auth/model integration suite;
- the project describes CKAN 2.11 modernisation but has no recorded CKAN 2.12.1
  integration result;
- term update does not apply `parent_id`, even though the edit flow supplies it;
- explicit self-parent, cycle and cross-taxonomy-parent validation was not found;
- uniqueness/error handling differs between create and update paths;
- the README describes narrower admin permissions than the implementation; and
- legacy imports and bundled older tree assets increase upgrade maintenance risk.

The PIDINST configuration also has overlapping taxonomy-related settings: theme
keys map logical taxonomy names, while a separate taxonomy organisation setting
does not appear to drive the extension's actual auth rule. These should be
consolidated or documented during dependency hardening.

### Recommendation

Core should not implement taxonomy tables, hierarchy actions, admin pages, seed
commands or SKOS import. Those capabilities already belong to `ckanext-taxonomy`.

Core may later provide a thin, optional, namespaced picker adapter if two consumers
need it. Such an adapter should discover the extension's public actions at runtime,
avoid direct model imports and return a clear capability-unavailable response when
the plugin is inactive. PIDINST's reference protection and propagation remain in
PIDINST.

Before CKAN 2.12.1 use, pin the taxonomy dependency to an exact reviewed revision,
add a real CKAN integration profile and fix hierarchy integrity in that project.
Until those tests pass, taxonomy compatibility with CKAN 2.12.1 is unverified.

## 3. Party management

### Current PIDINST design

PIDINST models a Party as a CKAN group with `group_type: party`. Its Scheming group
schema includes identity, ROR metadata, contacts, aliases, hierarchy and the fixed
instrument roles Owner, Funder and Manufacturer.

Party flows include:

- creation/editing of ROR-backed or local parties;
- ROR search, parent resolution and optional creation of missing parent parties;
- a local parent-party selector and hierarchy views;
- instrument form selectors filtered by role;
- snapshot fields for name, identifier, identifier type and selected contact data;
- package membership synchronisation so Party groups can support counts/facets;
- deletion guards for parties referenced by instruments; and
- asynchronous propagation of selected Party changes into instrument metadata.

The Party identifier stored in instrument composites is currently the group's slug,
with title and external identifiers stored as snapshots. Slugs can collide and can
be affected by naming policy. Changing this contract to group UUIDs would require a
deliberate compatibility and migration plan; it must not be folded into a Core
extraction.

### Permissions and security observations

Core CKAN group auth is extended so configured organisation admins can manage Party
groups, while ordinary visibility still relies on CKAN actions. Some PIDINST
endpoints explicitly require a logged-in user and then call group actions, and
read endpoints build visibility-aware trees.

Items to harden within PIDINST include:

- validate local hierarchy changes against self-parenting and cycles;
- define collision behaviour for generated slugs;
- ensure every mutating endpoint uses CKAN auth and the expected CSRF protection;
- replace or formally constrain `ignore_auth` internal calls;
- test private package visibility and group counts under all relevant roles; and
- replace daemon-thread propagation with a durable job mechanism before relying on
  it for authoritative updates.

The current five-minute Party-tree cache is an in-process dictionary invalidated by
group actions. Its version is worker-local, so separate web workers can serve
different cache generations. Auth-sensitive Party trees must not be placed in a
shared cache without including visibility context.

### Generic versus PIDINST-specific functionality

Potentially reusable:

- ROR v2 transport and result normalisation;
- lookup by query or canonical ROR identifier;
- bounded parent relationship resolution;
- an organisation result contract and configurable picker; and
- generic display helpers for a stored local ID plus external identifier snapshot.

PIDINST-specific:

- the Party group schema and fixed Owner/Funder/Manufacturer roles;
- owner versus manufacturer ROR filtering policy;
- automatic creation of ROR parent groups and upward role inheritance;
- instrument-to-group membership synchronisation and facets;
- contact overwrite policy;
- instrument composite field names; and
- deletion guards and propagation into instrument records.

### Recommendation

Party management should remain an optional PIDINST capability. Core should expose
only the ROR lookup provider and a role-neutral organisation picker. It should not
define Party roles, group schemas, hierarchy inheritance or dataset relationships.

A separate `ckanext-auscope-party` would become reasonable only when at least one
other repository has a concrete shared Party lifecycle, the same identity model and
an independent need to activate or migrate it. Creating it for a hypothetical reuse
case would add plugin, migration and compatibility overhead during the RAiD work.

## 4. Geographic validators

### Behaviour comparison

The main implementations are:

- Data: `ckanext/auscope_theme/logic/validation.py`;
- Sample: `ckanext/igsn_theme/logic/validators.py`; and
- PIDINST: `ckanext/pidinst_theme/logic/validators.py`.

| Behaviour | Data | Sample | PIDINST |
|---|---|---|---|
| Latitude | Converts to float, range -90 to 90 | Same | Same |
| Longitude | Converts to float, range -180 to 180 | Same | Same |
| Bounding box | Four values, coordinate ranges and strict min/max ordering | Same | Same |
| Point/area input | JSON feature collection selected by location type | Same | Same |
| Elevation | Read but not consistently validated | Numeric validation | Not present |
| EPSG | Presence check only | Presence check only | Presence check only |
| Spatial output | No conversion found in the reviewed validator | First feature converted with Shapely | First feature converted with Shapely |
| `noLocation` | Clears `location_data` | Clears `location_data` | Clears `location_data` |

The latitude, longitude and bounding-box helpers are nearly duplicated. An
additional `is_valid_bounding_box` helper appears unused in all three themes.

### Correctness and contract issues

The copied location validators have several behavioural ambiguities:

- selecting Point validates only features that already say `Point`; a collection
  containing only another geometry type can pass without a point being validated;
- the equivalent issue exists for Polygon/area selections;
- malformed GeoJSON can escape through direct dictionary indexing or produce
  inconsistent error handling;
- geometry validity, polygon ring closure, feature cardinality and a complete
  GeoJSON structural contract are not enforced;
- Sample and PIDINST index only the first feature, although `location_data` can
  contain multiple features, so displayed and indexed geometry can diverge;
- `noLocation` clears only one field and can leave stale EPSG, elevation or spatial
  values unless a consumer schema clears them elsewhere;
- EPSG is not checked for syntax or existence; and
- the map draws latitude/longitude coordinates but allows a different EPSG label
  without transforming coordinates, which can misdescribe the GeoJSON.

The rectangle UI attempts an antimeridian representation by increasing the eastern
longitude beyond 180, while backend longitude and bounding-box checks reject that
value and require strict west-less-than-east ordering. Antimeridian policy must be
made explicit before a shared area validator claims to support it.

### What belongs in Core

Core can safely own pure, namespaced functions for:

- finite latitude and longitude parsing and range validation;
- bounding-box parsing and ordering under an explicitly documented antimeridian
  policy;
- structural GeoJSON validation for supported geometry/feature types;
- deterministic normalisation that does not silently skip the wrong geometry type;
  and
- EPSG identifier syntax normalisation, separate from an optional provider lookup.

Consumer adapters must retain:

- source field names and error messages tied to a schema;
- whether location, elevation or EPSG is required;
- the meaning and clearing behaviour of `noLocation`;
- single- versus multi-feature policy;
- coordinate transformation policy; and
- conversion into the one geometry indexed by `ckanext-spatial`.

Core should not take a mandatory Shapely or `ckanext-spatial` dependency for these
primitives. Consumers already using a geospatial profile can perform geometry
validity and index transformation in their adapter. If more advanced shared
geometry operations are later proven necessary, they should be an optional extra
with explicit tests.

## 5. Architecture and compatibility assessment

### Dependency ownership

Core currently has no runtime extension dependencies, and its architecture keeps
business schemas and repository-specific validators out of the shared theme. The
proposal preserves the important part of that boundary: Core gains only generic,
opt-in contracts that have demonstrated reuse, not consumer schemas or domain
models.

| Capability | Owner/dependency |
|---|---|
| Vocabulary provider clients and generic picker | AuScope Core |
| Dataset/group schema and field mapping | Consumer extension plus `ckanext-scheming` |
| Composite value storage | Consumer plus `ckanext-composite` where used |
| Taxonomy persistence, hierarchy, actions, admin and import | `ckanext-taxonomy` |
| PIDINST taxonomy reference protection | PIDINST |
| Spatial indexing and query | `ckanext-spatial` |
| Pure coordinate/GeoJSON primitives | AuScope Core |
| Party groups, roles and instrument propagation | PIDINST |

No optional extension should be imported at Core module import time. Optional
integration must use public CKAN actions/helpers and capability detection. This
allows the base `auscope_core` plugin to load without taxonomy, composite or spatial
plugins.

### Public API and naming

New action, validator, route, template and JavaScript names must be prefixed with
`auscope_` or `auscope_core`. Recommended action contracts are:

- `auscope_vocabulary_search(provider, query, page, context)`; and
- `auscope_vocabulary_children(provider, identifier, context)`.

If HTTP routes are also needed for browser modules, use a versioned namespace such
as `/api/auscope_core/v1/vocab/<provider>`. Do not initially register the existing
`/api/proxy/fetch_*` paths in Core, because consumers already own those paths.

A normalised result should be deliberately small:

```json
{
  "id": "stable provider identifier",
  "label": "display label",
  "source": "for|epsg|gcmd|ror|taxonomy",
  "metadata": {}
}
```

Provider-specific response bodies should not leak through this API. Pagination,
errors and hierarchy capability need equally explicit contracts.

### Configuration and operations

External URLs, vocabulary versions, scheme allowlists, timeouts, result limits and
cache TTLs should be declared under
`ckanext.auscope_core.vocabulary.*`, preferably through CKAN's configuration
declaration interface. Secrets are not currently required by the reviewed
providers, but future credentials must remain server-side.

Search results are suitable for a small bounded, stale-tolerant cache. A per-process
cache is acceptable as an initial performance optimisation only if documented as
non-coherent; Redis is preferable when shared cache consistency is needed. Do not
cache provider failures for a long period, and do not reuse public vocabulary cache
designs for auth-sensitive Party trees.

Provider calls need fixed connect/read timeouts, maximum query lengths and pages,
scheme allowlists, response-size protection, consistent 4xx/5xx mapping and
structured logging without personal data. Retry only safe idempotent requests and
respect upstream throttling.

### CKAN version compatibility

Implementation should use CKAN 2.12.1 public plugin interfaces and actions as the
baseline. Exact integration tests are required before claiming support. The same
suite should then run against PIDINST's CKAN 2.11.4 target and, only when Data/Sample
migration work starts, CKAN 2.10.1.

Source similarity is not compatibility evidence. In particular:

- `ckanext-taxonomy` has not been verified here on CKAN 2.12.1;
- the frontend framework and Select2-related behaviour must be checked against the
  actual CKAN version, not assumed from existing themes;
- the taxonomy revision must be pinned rather than installed from a moving branch;
  and
- provider tests must mock external services, with optional separately recorded
  live smoke tests so CI is not dependent on ARDC, EPSG or ROR availability.

## 6. Recommended target architecture

### Proposed Core module structure

The exact filenames can be adjusted to existing package conventions, but the
ownership should remain clear:

```text
ckanext/auscope_core/
  logic/
    actions/vocabulary.py          # public CKAN action contracts
    auth/vocabulary.py             # public-read policy and future hooks
    validators/geographic.py       # pure, prefixed validation primitives
  services/vocabulary/
    base.py                         # provider protocol, result and error types
    for_ardc.py
    epsg.py
    gcmd_ardc.py
    ror.py
    cache.py                        # bounded optional caching
  views/vocabulary.py              # versioned browser API if actions are insufficient
  assets/js/
    vocabulary-picker-module.js    # opt-in, provider-neutral picker
  templates/snippets/auscope_core/
    vocabulary_picker.html
  tests/
    logic/test_geographic_validators.py
    services/vocabulary/test_*.py
    fixtures/vocabulary/*.json
```

There should be no `taxonomy` model or `party` model package in Core. A future
taxonomy picker adapter, if demonstrated by another consumer, belongs under an
optional integration namespace and calls taxonomy actions rather than its models.

### Candidate source material to adapt

These files are useful sources, but should be adapted into explicit contracts
rather than copied wholesale:

| Source | Reusable material | Keep out of Core |
|---|---|---|
| PIDINST `views.py` | GCMD allowlisting/deduplication; ROR v2 normalisation; provider error mapping | Instrument role filters, Party creation, local field-term search |
| Data/Sample theme `views.py` | Confirmation of shared FOR/EPSG/GCMD request shapes | Unnamespaced legacy routes and bare network calls |
| PIDINST `vocab-picker-module.js` | Composite/split picker concepts and duplicate prevention | Instrument field assumptions and URI guessing |
| PIDINST FOR/GCMD handler modules | Existing submitted-value formats | Hard-coded endpoint and field IDs |
| Three validator modules | Coordinate and bounding-box primitives | Schema tuple mutation, field names and spatial indexing policy |
| PIDINST Party snippets/actions | ROR result display and identity snapshots | Owner/Funder/Manufacturer behaviour and propagation |
| `ckanext-taxonomy` public actions | Optional search/tree integration contract | Models, CRUD/admin duplication and direct imports |

### Adoption without breaking current behaviour

1. Capture fixtures for existing provider responses, submitted forms and stored
   values before changing runtime code.
2. Add new namespaced Core actions/routes and opt-in snippets without removing any
   consumer endpoint.
3. Allow consumer JavaScript to receive its endpoint, provider and storage mapping
   as module options.
4. Migrate one field and repository at a time, asserting byte-equivalent or
   semantically equivalent stored values and unchanged edit round-trips.
5. Keep legacy consumer routes as compatibility shims during a declared transition
   window; remove them only after all callers are inventoried and tested.
6. Introduce no taxonomy or Party data migration as part of vocabulary adoption.
7. Record exact-version integration results separately for each CKAN target.

This sequence also avoids route conflicts when Core and an older consumer theme are
active together.

## 7. Prioritised implementation plan

Effort estimates are engineering days for implementation, focused tests and brief
documentation; they exclude environment remediation and review lead time.

### Stage 0: Capture existing contracts

- **Scope:** Record representative provider responses, form submissions, stored
  split/composite values and current validation outcomes.
- **Sources:** Existing schemas, proxy routes, JavaScript modules and a small sample
  of non-sensitive repository records.
- **Dependencies:** None beyond current test tooling.
- **Main risks:** Fixtures accidentally encode incidental markup or personal data.
- **Expected benefits:** Prevents silent storage/API changes during extraction.
- **Acceptance criteria:** Sanitised golden fixtures cover FOR, EPSG, GCMD, ROR,
  taxonomy-composite and geographic cases; current contracts are documented.
- **Effort:** 0.5-1.5 days.

### Stage 1: Shared geographic primitives

- **Scope:** Implement pure, prefixed latitude, longitude, bounding-box and basic
  GeoJSON validation in Core; do not change consumer schemas or spatial output.
- **Sources:** The three copied validator modules.
- **Dependencies:** Standard library and existing Core test tooling only.
- **Main risks:** Accidentally deciding antimeridian, multi-feature or `noLocation`
  policy in a generic helper.
- **Expected benefits:** Removes proven duplication with the smallest dependency and
  deployment risk; creates a tested base for later adapters.
- **Acceptance criteria:** Unit matrices cover boundaries, non-finite values,
  malformed values, geometry-type mismatch and bounding-box ordering; validators
  are namespaced; no optional extension is needed; no consumer behaviour changes.
- **Effort:** 1.5-3 days.

### Stage 2: Vocabulary service foundation with FOR and EPSG

- **Scope:** Add the provider/result protocol, namespaced search action or route,
  configuration, limits, timeouts, errors and mocked FOR/EPSG clients.
- **Sources:** Duplicated Data, Sample and PIDINST proxy routes.
- **Dependencies:** CKAN's available HTTP stack; no new extension dependency.
- **Main risks:** Upstream response drift and route compatibility.
- **Expected benefits:** Replaces the clearest external-service duplication and
  establishes the contract used by later providers.
- **Acceptance criteria:** Mocked success, empty, malformed, timeout and upstream
  failure tests pass; no bare unbounded request remains in the new service; legacy
  routes and stored values are unchanged.
- **Effort:** 3-5 days.

### Stage 3: GCMD search and hierarchy provider

- **Scope:** Add configured GCMD schemes, merged search and narrower-term traversal
  behind the common contract.
- **Sources:** PIDINST GCMD search/narrower routes and tree module.
- **Dependencies:** Stage 2; configured ARDC vocabulary revisions.
- **Main risks:** Dated ARDC paths, N+1 hierarchy requests and label/URI drift.
- **Expected benefits:** One maintained GCMD implementation for repository pickers
  and trees.
- **Acceptance criteria:** Allowlist, merge, deduplication, pagination and partial
  hierarchy failures have mocked tests; versions are configuration, not code.
- **Effort:** 3-5 days.

### Stage 4: Opt-in picker and first consumer migration

- **Scope:** Build a namespaced provider-neutral picker and migrate one low-risk
  field, preferably in the RAiD integration or a non-required field first.
- **Sources:** PIDINST vocabulary picker and Data/Sample split-field handlers.
- **Dependencies:** Stages 0 and 2; the consumer's existing form framework.
- **Main risks:** CKAN frontend-version differences, accessibility and edit
  round-trip regressions.
- **Expected benefits:** Demonstrates reuse without centralising schemas.
- **Acceptance criteria:** Keyboard/focus behaviour is checked; no-JavaScript failure
  is understandable; create/edit preserve the established identifier and label
  representation; old endpoint remains available during transition.
- **Effort:** 3-5 days.

### Stage 5: ROR lookup, without Party extraction

- **Scope:** Add ROR v2 search/direct-ID lookup, normalised relationships, bounded
  hierarchy resolution and the generic organisation picker.
- **Sources:** PIDINST ROR proxy and Data/Sample affiliation lookup.
- **Dependencies:** Stage 2 provider framework.
- **Main risks:** ROR API changes, rate limits and confusing lookup policy with
  repository role policy.
- **Expected benefits:** Removes old direct browser calls and gives all consumers a
  consistent server-side contract.
- **Acceptance criteria:** Canonical ID and URL lookup work; filters are supplied by
  the consumer; timeouts, depth, result count and caching are bounded; no Party is
  created by the Core action.
- **Effort:** 2-4 days.

### Stage 6: Stabilise taxonomy for PIDINST

- **Scope:** In the taxonomy project, pin a release/revision, add exact CKAN 2.12.1
  integration coverage and repair parent/cycle/uniqueness/auth-documentation gaps.
- **Sources:** Current AuScope `ckanext-taxonomy` fork and PIDINST seed/config.
- **Dependencies:** Dedicated taxonomy test database and CKAN 2.12.1 profile.
- **Main risks:** Database integrity and compatibility changes in an existing
  production dependency.
- **Expected benefits:** Reuses the existing extension with a supportable upgrade
  path rather than duplicating it in Core.
- **Acceptance criteria:** CRUD, tree, reparent, delete, auth and CLI seed/import
  tests pass on exact CKAN 2.12.1; the pinned revision and result are recorded.
- **Effort:** 3-6 days, outside Core.

### Stage 7: Harden PIDINST Party lifecycle

- **Scope:** Add hierarchy/collision checks, review mutation auth/CSRF, define a
  stable identity plan and replace daemon propagation with durable jobs.
- **Sources:** PIDINST Party actions, auth, cache, snippets and propagation modules.
- **Dependencies:** PIDINST deployment/job infrastructure; Stage 5 is useful but not
  required.
- **Main risks:** Existing slug references, private visibility and large propagation
  jobs.
- **Expected benefits:** Improves PIDINST reliability without imposing its domain on
  other repositories.
- **Acceptance criteria:** Existing role behaviour remains; cycles and collisions
  fail clearly; interrupted jobs resume or fail visibly; multi-worker cache and
  permission tests pass.
- **Effort:** 5-10 days, outside Core.

### Stage 8: Consumer geographic adapters

- **Scope:** Adopt Core primitives one consumer at a time and explicitly define
  GeoJSON cardinality, clearing, CRS and spatial-index conversion.
- **Sources:** Existing validators, map modules and Scheming schemas.
- **Dependencies:** Stage 1 and each consumer's geospatial dependencies.
- **Main risks:** Changing indexed geometry, search results or previously accepted
  malformed metadata.
- **Expected benefits:** Consistent validation while preserving repository-specific
  indexing and metadata rules.
- **Acceptance criteria:** Contract tests prove create/edit/search behaviour for
  existing valid records; invalid legacy cases have an explicit migration or
  grandfathering policy; tests use `solr-test` and `ckan_test` only.
- **Effort:** 3-6 days per consumer.

## Immediate recommendation

Start with **Stage 0 followed immediately by Stage 1: shared geographic validation
primitives**. The implementation issue should be narrowly titled along the lines of
"Add namespaced geographic validation primitives to AuScope Core." It should not
alter a schema, map widget, EPSG provider or `spatial` field.

This is the highest-confidence shared extraction, produces value within the RAiD
timeframe and leaves the more consequential vocabulary API and storage contracts
protected by fixtures before migration begins. Vocabulary work should then proceed
with FOR and EPSG, because those routes are already duplicated almost exactly in
all three reference implementations.
