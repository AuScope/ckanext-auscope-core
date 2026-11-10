# Issue #2: branding analysis of the reference repositories

Date: 2026-11-03. Branch `feature/2-shared-branding`, stacked on the unmerged
Issue #1 test-isolation and Issue #5 compatibility branches (ADR-027).

## Scope and method

Both reference repositories were inspected read-only. Their `git status --porcelain`
and `HEAD` were captured before and after the inspection, and the two snapshots were
identical:

| Repository | HEAD | Pre-existing changes (not ours) |
|---|---|---|
| `C:\MyFiles\040_Ckan\ckan-docker` (Data, Sample) | `2c10d5b0` | 7 modified, 1 untracked |
| `C:\MyFiles\140-PIDINST\AuScope-instrument-registry` | `974efdfd` | 4 modified, 6 untracked |

No `.env` files were opened. PIDINST `.env.example` was not read because it may hold
real DataCite credentials. Nothing was copied from it.

CKAN 2.12.1 was checked in the running `ckan-dev` container
(`/srv/app/src/ckan/ckan`: `templates/base.html`, `page.html`, `header.html`,
`public/base/css/main.css`, `lib/webassets_tools.py`, `config/environment.py`,
`config/config_declaration.yaml`).

## How branding is shared today

- **Data and Sample** (`ckanext-auscope-theme`, `ckanext-igsn-theme`) share files from a
  `ckan/src/shared/` directory. The Dockerfile copies it to `/shared`. Each plugin
  calls `add_template_directory("/shared/templates")` and
  `add_public_directory("/shared/public")`, and each `webassets.yml` points to
  absolute paths such as `/shared/public/shared_style.css`. These assets are not part
  of any Python package and only work inside that Docker image.
- **PIDINST** (`ckanext-pidinst-theme`) has its own copy of `shared/public`, plus a
  forked `shared_style.css` inside its own assets
  (`assets/css/shared_style.css`, 23 KB). It no longer uses the shared templates.
- Every theme overrides `base.html` with `{% ckan_extends %}` and
  `{% block styles %}{{ super() }}{% asset '<theme>/<theme>-css' %}`. This is the
  native pattern, and `auscope_core` will use it too.

## Branding assets found

| Asset | Data/Sample | PIDINST | Notes |
|---|---|---|---|
| `AuScope Logo.png` (1200×289, royal-blue wordmark plus mark, transparent) | yes | yes | Same MD5 (`863CE797…`). Reusable. |
| `AuScope Logo – Reversed.png` (1200×289, white) | yes (3 copies) | yes (2 copies) | Same MD5 (`9F591C42…`). The file name contains a space and an en dash. Reusable for dark backgrounds. |
| `AuScope Logo Icon.png` (mark only) | 282×289, 45.8 KB | 281×288, 7.4 KB | PIDINST has the newer, optimised copy. Both header overrides use it as the logo. Reusable. |
| `AuScope Logo _ NCRIS.png`, `auscope_ncris@2x.png` | yes | yes | Same files. Only the footer uses them, and the footer is Issue #3. Australian Government NCRIS branding rules apply. Not included in Issue #2. |
| `RS6235_…tifesr.jpg` (888 KB), `RS6242_…balfeti.jpg` (1.29 MB) | yes | yes | Homepage hero photos. Large, the photo credit and licence are unknown, and they are content rather than branding. Not included. |
| `CalibreWeb-Light/Medium` `.woff`/`.eot` | yes | yes | Calibre is a commercial typeface (Klim Type Foundry). Neither repository has a licence file or attribution for it. Redistributing it in a public package cannot be shown to be allowed, so it is not included. |
| Favicon | none | none | All sites currently show CKAN's default `ckan.ico`. |
| Font Awesome | CDN 5.15.1 (footer) | CDN 6.5.0 (`base.html`) | CKAN 2.12 already bundles Font Awesome. No extra CDN is needed. |

Licensing: the AuScope logos are AuScope Limited trademarks with no licence file
anywhere. The reference extensions are AGPL. That AGPL covers code, not the AuScope
brand marks.

## Colours and conventions (shared_style.css)

Both copies of `shared_style.css` define the same palette in `:root`. PIDINST's copy
is the newer one. It adds `font-display: swap`, Bootstrap grey fallbacks, a hover
colour for `.btn-primary`, a teal underline on the active nav item, and a teal accent
on the hero.

| Legacy variable | Value | Use |
|---|---|---|
| `--color-aus-royal-blue` | `#282572` | Primary brand colour: headings, buttons, nav hover |
| `--color-aus-royal-blue-bright` | `#2e2b8a` | `.btn-success`, badges |
| `--color-aus-royal-blue-dark` | `#221f61` | Hover and active states |
| `--bs-teal` (overridden) | `#59c2aa` | Accent: active nav underline, hero border |
| `--color-aus-black` | `#231f20` | Body and nav text |
| `--bs-gray` (overridden) | `#d8d9d7` | Footer and body background |
| `--color-background-default` | `#f2f2f1` | Masthead, `.main` and hero backgrounds |
| `--bs-red` / `--bs-tangerine` | `#ea1e31` / `#ec5661` | Danger buttons |
| (literal) | `#7e7caa` | Muted `em` and footer text |

Other conventions in the legacy stylesheet:

- Body font size is `1.063rem`. A long list of selectors is forced to that size.
- h1 and h2 use royal blue, h3 uses black.
- The masthead and account bar are light, with black links. Hovered nav links get a
  royal-blue background and white text.
- `.btn-primary` and `.btn-success` are recoloured royal blue with long selector
  lists copied from Bootstrap 4/5 output.

## Differences between Data/Sample and PIDINST

- PIDINST has a newer copy of the palette and stylesheet (summarised above). Data and
  Sample still use the original copy.
- PIDINST bundles the stylesheet as a theme asset. Data and Sample use the absolute
  `/shared` path.
- The header logo text and navigation differ by repository: "AuScope Data
  Repository" and "AuScope Instrument Registry", each with its own nav tabs. The
  footers differ in their NCRIS years and social links (Twitter vs Bluesky). Both are
  handled by Issue #3's native configuration and template blocks.
- `pidinst_theme.css` (26 KB) and `igsn_theme.css` are almost all product-specific:
  instrument cards, vocab pickers, facet sidebars, `.stages` and `.badge` variants.
  The badge palette uses Bootstrap's success, warning and info colours rather than
  brand colours.

## Reusable vs repository-specific

**Reusable (moves into `auscope_core`)**: the palette, the typography base (font
stack, size, heading colour), primary button and link colours, the light masthead
with royal-blue hover and active states, the page surface colour, logo sizing in the
masthead, and the logos.

A later check of the three public sites (computed styles, 2026-11-03) confirmed the
same surfaces everywhere: `#f2f2f1` masthead and content, `#d8d9d7` footer with
royal-blue text, and a white homepage search box over a royal-blue keyword strip.
The resulting baseline and the remaining differences are in
[design-baseline.md](design-baseline.md).

**Repository-specific (stays in each consumer)**: Leaflet, jsTree and DataTables
vendor bundles; map, composite-field, ROR, GCMD and DOI JS modules; scheming form
styles (`.composite-*`, `.ror-*`, `.schema-table`); instrument cards; facet sidebars;
the loader; `.stages` tweaks; repository navigation, authentication links, annual
reporting links and approved NCRIS artwork; RudderStack analytics.

**Issue #3** shares the header brand geometry, three-column footer and homepage
geometry. It deliberately leaves CKAN's `page.html` untouched and exposes native
blocks for consumer navigation, authentication, homepage content and footer
differences.

## Problems in legacy CSS not to copy

- `a { color: inherit }` and `a:active, a:focus { outline: 0 }` make links look like
  body text and remove keyboard focus indicators. This fails WCAG 2.4.7 and 1.4.1.
- White text on tangerine `#ec5661` measures 3.46:1, and white on `#ea1e31` measures
  4.44:1. Both fail AA for normal text.
- Muted `#7e7caa` on the grey footer `#d8d9d7` measures 2.77:1, which fails AA.
- Teal `#59c2aa` measures 1.93:1 on `#f2f2f1` and 2.16:1 on white. As the only
  active-state indicator it fails WCAG 1.4.11, which requires 3:1 for non-text
  elements.
- There are many `!important` rules, vendor-prefixed transitions, IE `.eot` fonts,
  hard-coded pixel sizes, and duplicated rule blocks (`.composite-content` appears
  twice).
- The stylesheet redefines Bootstrap variables (`--bs-teal`, `--bs-gray`,
  `--bs-red`) with different meanings. That silently changes every Bootstrap
  utility that uses them.

## CKAN 2.12.1 native theming facilities

- `main.css` is a Bootstrap 5 build (the banner says v5.1.3, but it includes the
  5.3-style `:root,[data-bs-theme=light]` variables). Pages read `--bs-body-*`,
  `--bs-link-color-rgb`, `--bs-link-hover-color-rgb`, `--bs-heading-color` and
  `--bs-primary(-rgb)`.
- Components expose their own variables: `.btn-primary` and `.btn-outline-primary`
  use `--bs-btn-*`, `.nav-pills` uses `--bs-nav-pills-link-active-bg`, and
  `.pagination` uses `--bs-pagination-*`. These can be themed without copying
  selectors.
- CKAN's own components use hard-coded colours rather than variables:
  `.masthead`/`.site-footer`/`.homepage .search-form` use `#005d7a` + `bg.png`,
  `.account-masthead` and `.homepage .tags` use `rgb(0,54,71)`, nav links use
  `#fff`, `.form-check-input:checked` uses `#206b82`, and `.main` uses `#eee`
  + `bg.png`. Recolouring these needs a few targeted selector overrides.
- CKAN sizes the logo with `.masthead .navbar .logo img { max-height: 60px;
  min-height: 55px; }` (specificity 0,3,1). Any AuScope logo sizing must use that
  selector and reset `min-height`/`max-height`, otherwise the logo is always 55-60 px
  tall. (Corrected after design review finding 3.)
- Other CKAN rules that affect the theme: `--bs-heading-color` defaults to `inherit`,
  which keeps the homepage search headings white on the dark search box;
  `.navbar-toggler:focus { outline: 0 }`; inside `max-width: 991.98px`,
  `.masthead .main-navbar ul li a:hover, … a:focus { color: #fff }`;
  `.homepage .module-feeds` and `.homepage .hero` use `#eee`/tile background images.
- `role="main"` is only on `home/index.html`, `home/about.html`, the
  `confirm_delete*.html` templates and the two-column `.primary` column in
  `page.html`. Pages that override the `primary` block lose it. `page.html` renders
  `<div class="main">` on every page, so `.main` is the reliable content anchor.
- `ckan.site_logo` (default `/base/images/ckan-logo.png`) and `ckan.favicon`
  (default `/base/images/ckan.ico`) are the native logo and favicon settings, used
  by `header.html` (`header_logo`) and `base.html` (`links`). Config defaults are
  filled in by `config_declaration.normalize()` before plugins' `update_config`
  runs.
- `ckan.site_custom_css` is rendered after all styles (`custom_styles` block). It is
  editable by sysadmins.
- `ckan.theme` replaces the core `css/main` asset. Not needed, because the AuScope
  styles layer on top of `main.css`.
- Webassets: `include_asset` loads `extra.preload` dependencies first and keeps
  include order. An unknown asset name only logs an error, so tests must check the
  rendered `<link>`. The first registration of a bundle name wins.
- `page.html` already has a skip link (`.visually-hidden-focusable`), and Bootstrap
  already handles `prefers-reduced-motion` for its own transitions.
- An SCSS rebuild of CKAN's Bootstrap would need a Node/Sass toolchain and a copy of
  CKAN's SCSS, which makes every CKAN upgrade harder. Plain CSS custom properties
  layered over `main.css` avoid both.
