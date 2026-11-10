# Reusable UI component analysis

Issue #4 compared the Data and Sample themes in `ckan-docker` with the PIDINST
theme. The repositories were inspected read-only. This review uses CKAN 2.12.1 as
the baseline and treats a copied override as a maintenance cost, not automatically
as a component worth sharing.

## Findings

| Area | Data | Sample | PIDINST | Core decision |
|---|---|---|---|---|
| Dataset and resource presentation | Mostly CKAN presentation plus Data-specific declaration/upload changes | Sample hierarchy and tabular results | Instrument lifecycle, family, map and DOI presentation | Keep CKAN's `package_item.html` and `resource_item.html`; product additions remain in consumers |
| Buttons, notices and badges | Bootstrap/CKAN classes | Bootstrap/CKAN classes plus product wording | Bootstrap/CKAN classes plus lifecycle tombstones | Use native `.btn`, `.alert` and `.badge`; no wrapper with no shared behaviour |
| Forms and Scheming | Declaration, fixed owner and upload workflow | Sample parent/contact and collection workflow | PIDINST composites, vocabularies, parties, maps and DOI fields | Keep schemas and form snippets in consumers; use Scheming's standard snippets for ordinary fields |
| Search and facets | CKAN link facets with a repository-specific exclusion list | Custom multi-select facet | The same custom multi-select facet; additional instrument-only checkbox/tree/date filters | Provide the multi-select as the opt-in namespaced `facet_select.html`; default searches should keep CKAN's native facet snippet |
| Organisations and groups | Standard organisations with Data-specific visibility rules | Collections, membership requests and role presentation | Parties/organisations and instrument-specific filters | Keep CKAN's organisation/group presentation; workflows and labels remain in consumers |
| JavaScript | A placeholder theme module | Select2 facet module, sample tree, DataTables | Same Select2 facet module plus PIDINST-specific map, taxonomy, party, DOI and lifecycle modules | The shared facet no longer needs JavaScript; do not copy placeholder, vendor or product modules |

Several Sample and PIDINST files are byte-for-byte identical, including broad
`page.html`, dashboard, membership, Scheming organisation/contact and vendor
overrides. They are deliberately not moved. Some duplicate CKAN templates, while
the rest encode public/private policy, collection terminology, contact defaults or
membership workflows. Sharing those files would put repository behaviour into the
theme and increase the CKAN upgrade surface.

## Extracted component

`snippets/auscope_core/facet_select.html` is a consumer-invoked alternative to
CKAN's link facet. It is based on the shared Sample/PIDINST use case but replaces
inline CSS, Select2 initialisation and forced page reloads with a native GET form.
It therefore works without JavaScript, preserves repeated query parameters, resets
pagination when filters change, exposes a programmatic label and instructions, and
uses CKAN/Bootstrap classes plus namespaced layout CSS.

The snippet is opt-in because CKAN's built-in `snippets/facet_list.html` remains the
preferred default and supports individual add/remove links and "show more". Data
and RAiD should use the built-in facet unless they establish a genuine multi-select
need. Sample and PIDINST can replace their copied facet template by calling the
shared snippet from their search/facet block. Consumers can customise labels,
empty text, action URL, preserved query parameters and an additional class without
forking Core; they can also override the namespaced template from their own
template path when markup changes are necessary.

No third-party JavaScript or CSS dependency is added.
