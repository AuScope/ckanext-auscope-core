# Shared FOR and EPSG vocabulary review

- Status: implemented in AuScope Core
- Reviewed: 18 November 2026
- Reference revisions: PIDINST `974efdfd25c7`; Data/Sample
  `2c10d5b0cb1e`; RAiD `1463b1875199`

## Summary

Data, Sample and PIDINST contain effectively identical, unauthenticated proxy
integrations for ANZSRC 2020 Fields of Research (FOR) and the EPSG Registry. The
browser modules also share the same split-field storage contracts. These provider
calls and response normalisation are genuinely reusable; schemas, field names,
map policy and submitted value shapes remain consumer responsibilities.

RAiD contains a copy of the PIDINST theme implementation but no separate RAiD
schema integration. It therefore supplies no additional provider contract.

## Comparison matrix

| Concern | Data | Sample | PIDINST | Core decision |
|---|---|---|---|---|
| FOR provider | ARDC LDA, `anzsrc-2020-for` | Same | Same proxy and picker assets; current instrument schema does not use them | Shared ANZSRC 2020 client |
| FOR request | `_page`, `labelcontains`; no timeout | Same | Same | First-page bounded search; exact 2/4/6-digit lookup; connect/read timeouts |
| FOR response | `result.items[]`; `notation`, `prefLabel._value`, optional `definition` | Same | Same | `{id, label, description?, vocabulary}` |
| FOR storage | comma-separated notations plus JSON label list in `fields_of_research` | Same | Picker uses the same split-field convention | Consumer-owned; Core returns notation strings |
| EPSG provider | EPSG Registry `api/v1/CoordRefSystem` | Same | Same | Shared EPSG CRS client |
| EPSG request | `keywords`, `page`, `pageSize=50`, `includeDeprecated=false`; no timeout | Same | Same | Bounded name search and generic CRS code lookup; connect/read timeouts |
| EPSG response | `Results[]`; numeric `Code`, `Name`, `Type` | Same | Same | Codes converted losslessly to strings; no consumer-specific type filter |
| EPSG storage | numeric code string plus `"code - name"` label | Same | Same; defaults the form to 4326 | Consumer-owned; Core returns code and name separately |
| Routes | `/api/proxy/fetch_terms`, `/api/proxy/fetch_epsg` | Same paths | Same paths | New versioned namespace; legacy aliases are not registered |
| Cache/errors | Browser Select2 cache only; upstream bodies passed through; no timeout/exception handling | Same | Same | No server cache yet; safe validation and stable 4xx/5xx mapping |

## Existing implementations

### FOR

The three themes call:

`https://vocabs.ardc.edu.au/repository/api/lda/anzsrc-2020-for/concept.json`

with `_page` and `labelcontains`. No authentication is required. The representative
current response is Linked Data API JSON with a `result.items` list. Each concept
has a stable ANZSRC notation, an authoritative URI such as
`https://linked.data.gov.au/def/anzsrc-for/2020/3705`, a preferred label and
sometimes a definition, broader and narrower links. Two-, four- and six-digit
notations represent the hierarchy levels. The Core lookup uses ARDC's
`resource.json?uri=...` endpoint and constructs the URI only after validating the
notation.

Relevant sources:

- PIDINST `ckan/src/ckanext-pidinst-theme/ckanext/pidinst_theme/views.py:324`
- PIDINST `.../assets/js/for-fields-handler-module.js:1`
- Data `ckan/src/ckanext-auscope-theme/ckanext/auscope_theme/views.py:14`
- Sample `ckan/src/ckanext-igsn-theme/ckanext/igsn_theme/views.py:404`
- shared Data/Sample `ckan/src/shared/public/base/js/for-fields-handler-module.js:1`
- Data schema `.../data_repository_schema.yaml:172`
- Sample schema `.../sample_repository_schema.yaml:260`

The legacy picker searches after three characters, maps `notation` to the Select2
ID and `prefLabel._value` to display text, submits comma-separated codes, and keeps
the label snapshots as a JSON list. Core deliberately does not reproduce that UI
or storage mapping.

### EPSG

The themes call:

`https://apps.epsg.org/api/v1/CoordRefSystem/`

with `keywords`, zero-based `page`, `pageSize=50` and
`includeDeprecated=false`. No authentication is required. Search responses contain
`Results`, `Page`, `PageSize` and `TotalResults`; each result includes a numeric
`Code`, `Name`, `Type`, descriptive fields and detail links. Generic lookup is
available at `/api/v1/CoordRefSystem/{code}`.

Relevant sources:

- PIDINST `ckan/src/ckanext-pidinst-theme/ckanext/pidinst_theme/views.py:312`
- PIDINST `.../assets/js/map-module.js:528`
- Data `ckan/src/ckanext-auscope-theme/ckanext/auscope_theme/views.py:38`
- Sample `ckan/src/ckanext-igsn-theme/ckanext/igsn_theme/views.py:392`
- shared Data/Sample `ckan/src/shared/public/base/js/map-module.js`
- PIDINST schema `.../instrument_schema.yaml:540`
- Data schema `.../data_repository_schema.yaml:264`
- Sample schema `.../sample_repository_schema.yaml:323`

The legacy UI filters search results to `geographic 2D` and `compound`, then stores
the numeric code separately from a `"code - name"` label. That filter is map and
schema policy, so the shared client returns all non-deprecated CRS search results.

## Reliability and compatibility findings

The legacy proxies interpolate user input into URLs, make bare `requests.get`
calls, pass provider response bodies through, and have no server-side bounds,
response validation or exception handling. Their Select2 `cache: true` setting is
browser-local. None retries or requires provider authentication.

Core now sends query parameters separately, uses fixed connect/read timeouts,
limits query length and result count, validates response shape and identifier
syntax, streams only the configured response byte limit, closes responses, and
maps failures without exposing provider details. Exact code searches use lookup
endpoints; empty provider result sets are normal successful responses. HTTP 404
lookups become not-found results, while malformed successful responses remain
upstream failures. Client and CKAN startup validation enforce positive timeouts and
bounds, `default_limit <= max_limit`, and valid HTTP/HTTPS provider URLs. A server
cache was not added because no existing behaviour demonstrates suitable freshness
or invalidation requirements.

The implementation uses CKAN 2.12.1's `IBlueprint` and `IConfigDeclaration`
interfaces and CKAN's installed HTTP stack. It has no optional CKAN-extension or
geospatial dependency. CKAN 2.11.4 and 2.10.1 remain unverified until the same
integration suite runs against those exact versions.

## Reusable boundary

Core owns the provider clients, normalized results, validation, limits, timeouts,
safe error mapping and versioned read APIs. Consumers still choose permitted
vocabularies, hierarchy levels and CRS types; map results to schema fields; decide
requiredness; store label snapshots; and integrate autocomplete or maps. Existing
consumer routes are unchanged to permit incremental migration.
