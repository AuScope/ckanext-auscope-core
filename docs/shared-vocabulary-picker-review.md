# Shared FOR and EPSG picker review

- Reviewed: 18 November 2026
- Reference revisions: PIDINST `974efdfd25c7`; Data/Sample
  `2c10d5b0cb1e`; RAiD `1463b1875199`
- Scope: read-only review; no consumer repository was modified

## Summary

Data and Sample use the same jQuery/Select2 3-style FOR and EPSG widgets from a
shared directory. PIDINST carries near-identical copies, although its current
instrument schema exposes the EPSG fields and does not currently declare the FOR
field pair. RAiD contains a copy of the PIDINST theme rather than an independent
RAiD picker integration. All implementations couple provider response fields,
global DOM IDs and consumer storage fields in one module.

The reusable boundary is an opt-in picker that consumes Core's normalized API and
emits normalized selections plus configured derived hidden fields. Consumer
extensions still choose Scheming field names, requiredness, permitted FOR levels
or CRS types, default values and final validation.

## Existing behaviour

| Concern | FOR | EPSG |
|---|---|---|
| Library | CKAN's installed jQuery and Select2, using the Select2 3 `query` API | Same |
| Template | `scheming/form_snippets/fields_of_research_field.html` | Embedded in `spatial_fields.html`; enhanced by the larger map module |
| Search trigger | Three entered characters, nominal 250 ms delay | Zero entered characters, nominal 250 ms delay |
| Legacy endpoint | `/api/proxy/fetch_terms` | `/api/proxy/fetch_epsg` |
| Result mapping | `notation` is the Select2 ID; `prefLabel._value` is text | `Code` is the ID; text is `"code - name"`; only `geographic 2D` and `compound` search results are retained |
| Cardinality | Multiple | Single |
| Identifier storage | `fields_of_research_code`: Select2's comma-separated notations | `epsg_code`: numeric code represented as form text |
| Label storage | `fields_of_research`: JSON array of label snapshots | `epsg`: one `"code - name"` snapshot |
| Edit initialization | Split codes on commas, parse label JSON and pair by array index | Read code and label fields; if code is empty, force `4326` / `4326 - WGS 84` |
| Removal | Select2 token removal updates the label JSON on `change` | Select2 change replaces the label field |
| Pagination | Tracks provider page/next fields and asks Select2 to load more | Computes `more` from page size and total results |
| Error handling | No AJAX error callback or user feedback | No AJAX error callback or user feedback |
| Stale responses | No abort or sequence protection | No abort or sequence protection |

Data and Sample declare the FOR fields as a visible code field and a hidden label
snapshot field. Their schemas also declare `epsg_code` and hidden `epsg`; the map
form owns the visible EPSG control. PIDINST declares the EPSG pair in its current
instrument schema. Its FOR JavaScript and template are present but are not wired
to that schema. The copied RAiD source has the same PIDINST contracts and supplies
no separate RAiD schema evidence.

## Templates, accessibility and validation

The FOR templates render a label, required marker, help text and server errors,
but hard-code `fields_of_research_code` and rely on the separate hidden
`fields_of_research` field being present elsewhere. The JavaScript uses global ID
selectors, so more than one picker or renamed fields are unsafe. The EPSG control
is similarly tied to global `#field-epsg_code` and `#field-epsg` selectors inside
the map module.

Select2 supplies keyboard navigation and token removal. The legacy modules add no
live loading, no-results or failure status, do not protect against out-of-order
responses, and do not validate response shapes before mapping. Duplicate handling
is left to Select2. Server-side Scheming validators largely accept the submitted
browser values; provider membership is not established by these widgets.

## Asset conventions

PIDINST registers one `pidinst_theme-js` Webassets bundle containing vendor
Leaflet/DataTables/JSTree files and all theme modules, with `vendor/jquery` and
`vendor/bootstrap` preloaded. Data and Sample expose the corresponding scripts
from their shared public directory and theme bundles. The picker code itself does
not introduce a separate JavaScript dependency. Core should therefore use a small
opt-in Webassets bundle that preloads CKAN's jQuery and reuses CKAN's installed
Select2 rather than shipping another copy.

## Core implementation boundary

The Core picker:

- searches `/api/auscope-core/v1/vocabularies/{for|epsg}` and consumes only
  normalized `{id, label, description?, vocabulary}` entries;
- uses consumer-provided field names and initial `{id, label}` values;
- submits the main identifier field in the established Select2 form shape (one
  ID, or comma-separated IDs for multiple selection);
- can map selections to additional hidden fields using `id`, `label`, readable
  `display`, or normalized `selection` values with `first`, `csv`, or `json`
  serialization;
- aborts superseded requests and ignores stale responses;
- reports loading, no-result and safe error states through an ARIA live region;
- keeps consumer policy and schema validation outside Core.

The API exposes only bounded first-page searches and no `has_more` value. The
picker consequently returns `more: false` and expects users to refine their
query. It does not infer or fake pagination. A future pagination requirement needs
an explicit v1-compatible response contract before UI changes are made.

## Adoption implications

Data and Sample can reproduce their FOR storage unchanged by naming the main field
`fields_of_research_code` and mapping labels as JSON to `fields_of_research`.
Their EPSG contract is preserved by naming the main field `epsg_code` and mapping
the first readable display value to `epsg`. Existing defaults and CRS type filters
remain consumer policy.

PIDINST can replace only its EPSG portion first, leaving the map and schema fields
unchanged, and can adopt FOR later if its schema exposes those fields. RAiD should
define its own schema mapping rather than inheriting the copied PIDINST global
selectors. No existing records need migration when initial values are constructed
from the stored code and label fields.
