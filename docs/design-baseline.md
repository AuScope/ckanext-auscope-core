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
| Masthead and account bar | Light grey `#f2f2f1`, black links, royal-blue hover with white text and royal-blue active underline; no decorative border | `--auscope-masthead-*`, `--auscope-account-masthead-bg`, `--auscope-nav-active-*` |
| Footer | Grey `#d8d9d7`, royal-blue text, headings, links and focus ring (9.28:1) | `--auscope-footer-bg`, `--auscope-footer-color` |
| Homepage search | Flat white search box with black heading; royal-blue popular-tags strip with white heading | `--auscope-home-search-*` |
| Typography | Calibre family names with system fallbacks, 1.063rem body/1.5 line height; h1 2rem/500, h2 1.75rem/400, h3 1.313rem/300 | `--auscope-font-*`, `--auscope-heading-*` |
| Links | Royal blue, dark on hover; underlined in running text and in the footer | `--auscope-color-primary(-hover)` |
| Buttons | `.btn-primary` and `.btn-outline-primary` royal blue, dark hover; other variants keep Bootstrap semantics | Bootstrap `--bs-btn-*` |
| Pagination, nav pills, checked inputs, focused inputs | Royal blue | Bootstrap `--bs-pagination-*`, `--bs-nav-pills-*` |
| Focus | 3 px solid outline, 2 px offset, royal blue; white on the popular-tags strip | `--auscope-focus-ring-*` |
| Logo and title | AuScope mark at 60 px (44 px below 576 px), repository title at 1.5rem and navigation at 1.2rem; centred and stacked above the native toggler on mobile | `--auscope-logo-*`, `--auscope-header-*` |

## Shared and repository-owned elements

| Shared by all repositories | Configurable or overridable | Repository-specific |
|---|---|---|
| AuScope mark/title structure, CKAN account/nav/search framework, responsive header geometry | Repository title and mark through `ckan.site_title` / `ckan.site_logo`; brand sub-blocks | Navigation destinations; AAF and other authentication links; contact workflow |
| Three-column Contact Us, Funding and Community footer; current AuScope contact details and social links; acknowledgement | Every column, funding-artwork slot, community/reporting links, social links, acknowledgement and optional CKAN footer meta blocks | Reporting-year links, approved NCRIS artwork and any repository-specific contact text |
| Full-width CKAN homepage search and responsive two-column lower area | Native `search`, `promoted`, `featured_group` and `featured_organization` blocks | Homepage copy, imagery, promoted records and business workflows |
| CKAN's standard common-page layout and a small namespaced section macro | Native `page.html` blocks | Schemas, forms, record cards and domain workflows |

## Differences from the legacy sites

"Legacy" is the computed style on all three live sites unless a site is named.

| Area | Legacy | Core | Decision | Scope |
|---|---|---|---|---|
| Footer colour | Grey `#d8d9d7`, royal-blue text | Was royal blue with white text; now grey with royal-blue text | Aligned (ADR-028) | Issue #2, fixed |
| Footer muted text | `#7e7caa` on grey (2.77:1) | Not provided | Deliberate: fails WCAG AA; footer content is Issue #3 | Issue #3 |
| Footer content | Contact details, funding, NCRIS logo, reporting links, social icons, acknowledgement | Same three columns, established text and current social links; complete acknowledgement; no CKAN attribution by default | Aligned. Reporting links stay with consumers; NCRIS image excluded because redistribution permission was not established | Issue #3 |
| Masthead background | `#f2f2f1`, no border | `#f2f2f1`, no border | Aligned; the earlier teal line was removed because it was not part of the established sites | Issue #3 |
| Header logo and title | Icon plus repository name text | `ckan.site_logo` icon plus native `ckan.site_title` | Aligned without duplicate configuration | Issue #3 |
| Header sizing and mobile geometry | 60 px mark, approximately 1.5rem title and 1.2rem nav; centred stacked brand and left toggler on mobile | Same, using CKAN's existing header DOM and collapse behaviour | Aligned without copying the legacy header | Issue #3 |
| Homepage search and cards | Flat white box with black heading, royal-blue keyword strip; borderless hero box and teal promotion accent | Same geometry, colours and flat treatment; CKAN's accessible "Popular tags" wording | Aligned; CKAN terminology and tag route retained | Issues #2 and #3 |
| Font family | Calibre Light/Medium web fonts | Same family names with Inter/Segoe UI/Roboto/Arial fallbacks | Supported, but files remain consumer-supplied because no redistribution grant was found | Deliberate |
| Body size and text colour | 1.063rem; CKAN `#333` | 1.063rem; brand black `#231f20` | Size aligned; brand black retained for 14.55:1 contrast on the surface | Issue #3 |
| Heading scale | h1 32 px/500, h2 28 px/400, h3 21 px/300 black | Same sizes and weights; h1/h2 royal blue and h3 black | Aligned through tokens | Issue #3 |
| Links | `a { color: inherit }`, no focus outline | Royal blue, prose underlined, focus outline | Deliberate (ADR-025) | Deliberate |
| Active nav indicator | Teal underline (PIDINST) | Royal-blue underline | Deliberate: teal is 1.93:1 on the surface (ADR-025) | Deliberate |
| Primary buttons | Royal blue, dark hover | Same | Matches | n/a |
| Success and danger buttons | Royal blue / tangerine | Bootstrap semantics | Deliberate: white on tangerine is 3.46:1 (ADR-025) | Deliberate |
| Pagination active | CKAN teal `rgb(32, 107, 130)` | Royal blue | Deliberate brand consistency | Deliberate |
| Facet headings, tag pills | CKAN `#f6f6f6`, royal-blue heading; pill `#f6f6f6` | Same (CKAN defaults with core heading colour) | Matches | n/a |
| Resource format badges, activity stream | CKAN blue/teal | CKAN blue/teal | Deferred | Issue #4 |
| Cards, composite fields, instrument cards, schema tables, stages | Legacy component CSS | Not provided | Deferred or repository-specific | Issue #4 / consumer |
| Body background below the footer | `#d8d9d7` | `#d8d9d7` | Aligned by styling `body` directly without mapping `--bs-body-bg` | Issue #3 |

## Customising the homepage search

The homepage search form (`.homepage .module-search .search-form`, tokens
`--auscope-home-search-bg` and `--auscope-home-search-color`) assumes a light
background. Its heading is brand black and its focus ring uses royal blue. A
consumer that makes it dark must also set `--bs-heading-color` and
`--auscope-focus-ring-color` on that selector, per the dark-surface rule in
`AGENTS.md`.

## Known limitations

- Calibre remains a consumer-supplied font. No redistribution permission or font
  licence was present in either reference repository, so Core uses system fallbacks
  unless a licensed consumer declares `Calibre-light` and `Calibre-Medium`.
- The footer uses text for NCRIS funding rather than shipping the legacy NCRIS
  image because no redistribution permission was found. Consumers may add an
  approved asset through `auscope_footer_funding_branding` and must record its
  licence. Annual NCRIS reporting links remain consumer content because their years
  and destinations differ between the repositories.
- No live Sample record page was captured: the capture script found no dataset link
  on the Sample list page. Its home and list pages match the Data Repository.
