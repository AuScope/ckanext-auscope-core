# Shared design baseline

The visual baseline that `auscope_core` gives every AuScope CKAN repository (Data,
Sample, PIDINST, RAiD) on CKAN 2.12.1. Values live in
`ckanext/auscope_core/assets/css/tokens.css`; this page explains them. The aim is one
maintainable AuScope look, not a pixel copy of any legacy site.

Compared on 2026-11-03 against the public sites
`repository.data.auscope.org.au`, `sample.data.auscope.org.au` and
`pidinst.data.auscope.org.au` (computed styles read in headless Edge, GET only) and
against the reference stylesheets (`ckan/src/shared/public/shared_style.css` and
PIDINST's fork). The three live sites render the same palette and surfaces.

## Baseline

| Element | Baseline | Tokens |
|---|---|---|
| Brand colours | Royal blue `#282572` (primary), dark `#221f61` (hover), black `#231f20` (text), grey `#d8d9d7`, light grey `#f2f2f1`, white; teal `#59c2aa` decorative only | `--auscope-color-*` |
| Page surface | Light grey `#f2f2f1` behind white CKAN modules | `--auscope-color-surface` |
| Masthead and account bar | Light grey `#f2f2f1`, black links, royal-blue hover with white text, royal-blue active underline; 4 px teal line under the masthead | `--auscope-masthead-*`, `--auscope-account-masthead-bg`, `--auscope-nav-active-*` |
| Footer | Grey `#d8d9d7`, royal-blue text, headings, links and focus ring (9.28:1) | `--auscope-footer-bg`, `--auscope-footer-color` |
| Homepage search | White search box, royal-blue heading; royal-blue popular-tags strip with white heading | `--auscope-home-search-*` |
| Typography | System font stack, 1rem body, line height 1.5, royal-blue headings (CKAN sizes and weights) | `--auscope-font-*`, `--auscope-color-heading` |
| Links | Royal blue, dark on hover; underlined in running text and in the footer | `--auscope-color-primary(-hover)` |
| Buttons | `.btn-primary` and `.btn-outline-primary` royal blue, dark hover; other variants keep Bootstrap semantics | Bootstrap `--bs-btn-*` |
| Pagination, nav pills, checked inputs, focused inputs | Royal blue | Bootstrap `--bs-pagination-*`, `--bs-nav-pills-*` |
| Focus | 3 px solid outline, 2 px offset, royal blue; white on the popular-tags strip | `--auscope-focus-ring-*` |
| Logo | Full AuScope wordmark, 48 px tall (36 px below 576 px) | `--auscope-logo-height(-sm)` |

## Differences from the legacy sites

"Legacy" is the computed style on all three live sites unless a site is named.

| Area | Legacy | Core | Decision | Scope |
|---|---|---|---|---|
| Footer colour | Grey `#d8d9d7`, royal-blue text | Was royal blue with white text; now grey with royal-blue text | Aligned (ADR-028) | Issue #2, fixed |
| Footer muted text | `#7e7caa` on grey (2.77:1) | Not provided | Deliberate: fails WCAG AA; footer content is Issue #3 | Issue #3 |
| Footer content | Contact, funding, NCRIS logo, socials, acknowledgement | Three accessible columns for contact, NCRIS funding and community links, plus acknowledgement, text CKAN attribution and language selector | Shared content aligned; NCRIS image excluded because redistribution permission was not established | Issue #3 |
| Masthead background | `#f2f2f1`, no border | Was white; now `#f2f2f1` with a teal line | Colour aligned (ADR-028); teal line kept as the brand accent | Issue #2, fixed |
| Header logo and title | Icon plus repository name text | `ckan.site_logo` icon plus native `ckan.site_title` | Aligned without duplicate configuration | Issue #3 |
| Nav link size | 1.2rem | CKAN size | Deferred with the header | Issue #3 |
| Homepage search box | White box, black heading, royal-blue keyword strip; full-width layout | White box, royal-blue heading and keyword strip; full-width layout; CKAN's accessible "Popular tags" wording | Colours and geometry aligned; CKAN terminology and tag route retained | Issues #2 and #3 |
| Font family | Calibre (Light/Medium web fonts) | System font stack | Deliberate: no redistribution licence for Calibre (ADR-024) | Deliberate |
| Body size and text colour | 1.063rem; CKAN `#333` | 1rem; brand black `#231f20` | Deliberate: Calibre's small x-height needed the larger size; brand black has higher contrast (14.55:1 on the surface) | Deliberate |
| Heading scale | h1 32 px/500, h2 28 px/400, h3 21 px/300 black | CKAN sizes and weights, royal blue | Deliberate: the light weights were tuned for Calibre and look thin in system fonts; revisit if a licensed brand font is adopted | Deliberate |
| Links | `a { color: inherit }`, no focus outline | Royal blue, prose underlined, focus outline | Deliberate (ADR-025) | Deliberate |
| Active nav indicator | Teal underline (PIDINST) | Royal-blue underline | Deliberate: teal is 1.93:1 on the surface (ADR-025) | Deliberate |
| Primary buttons | Royal blue, dark hover | Same | Matches | n/a |
| Success and danger buttons | Royal blue / tangerine | Bootstrap semantics | Deliberate: white on tangerine is 3.46:1 (ADR-025) | Deliberate |
| Pagination active | CKAN teal `rgb(32, 107, 130)` | Royal blue | Deliberate brand consistency | Deliberate |
| Facet headings, tag pills | CKAN `#f6f6f6`, royal-blue heading; pill `#f6f6f6` | Same (CKAN defaults with core heading colour) | Matches | n/a |
| Resource format badges, activity stream | CKAN blue/teal | CKAN blue/teal | Deferred | Issue #4 |
| Cards, composite fields, instrument cards, schema tables, stages | Legacy component CSS | Not provided | Deferred or repository-specific | Issue #4 / consumer |
| Body background below the footer | `#d8d9d7` | CKAN white | Left: mapping `--bs-body-bg` would also recolour form inputs; the footer is the last element on CKAN pages | Issue #3 |

## Customising the homepage search

The homepage search form (`.homepage .module-search .search-form`, tokens
`--auscope-home-search-bg` and `--auscope-home-search-color`) assumes a light
background. Its heading and focus ring use the global royal blue. A consumer that
makes it dark must also set `--bs-heading-color` and `--auscope-focus-ring-color` on
that selector, per the dark-surface rule in `AGENTS.md`.

## Known limitations

- The footer uses text for NCRIS funding rather than shipping the legacy NCRIS
  image because no redistribution permission was found. Consumers may add an
  approved asset by overriding `auscope_footer_funding` and recording its licence.
- No live Sample record page was captured: the capture script found no dataset link
  on the Sample list page. Its home and list pages match the Data Repository.
