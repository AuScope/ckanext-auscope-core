# Asset licences and attribution

Licensing and provenance for the files under `public/auscope_core/` and under
`assets/`. Every file in `public/auscope_core/images/` must have an entry here
(checked by `tests/test_theme_css.py`).

Source repository for the images (read-only reference, PIDINST):
`AuScope-instrument-registry`, directory `ckan/src/shared/public/base/images/`, at
commit `974efdf`.

## AuScope logos

| File | Original file name | MD5 | Size |
|---|---|---|---|
| `images/auscope-logo.png` | `AuScope Logo.png` | `863CE79762B91E98569D7E1A6F95776C` | 20125 B, 1200×289 |
| `images/auscope-logo-reversed.png` | `AuScope Logo – Reversed.png` | `9F591C422814FFF46F28B2BA210525FA` | 17694 B |
| `images/auscope-logo-icon.png` | `AuScope Logo Icon.png` | `B3D11EB1B451142504D5C64094052607` | 7392 B |

- Owner: © AuScope Limited. The AuScope name and logo are trademarks of AuScope
  Limited. All rights reserved.
- Included for use by AuScope services. Not covered by any licence chosen for this
  repository's code (none has been chosen yet; see ADR-011 in `docs/decisions.md`).
- Changes: copied unmodified apart from renaming to kebab-case file names.

## Favicon

| File | Derived from |
|---|---|
| `images/auscope-favicon.png` | `images/auscope-logo-icon.png` |

64×64 RGBA PNG. The icon was fitted with Pillow `thumbnail(LANCZOS)` and centred on
a transparent square. Generated once in the `ckan-dev` container (Pillow 12.3.0) with:

```
podman compose exec -w /srv/app/src_extensions/ckanext-auscope-core/ckanext/auscope_core/public/auscope_core/images ckan-dev python -c "from PIL import Image; s=Image.open('auscope-logo-icon.png').convert('RGBA'); s.thumbnail((64, 64), Image.LANCZOS); o=Image.new('RGBA', (64, 64), (0, 0, 0, 0)); o.paste(s, ((64 - s.width) // 2, (64 - s.height) // 2), s); o.save('auscope-favicon.png', optimize=True)"
```

Owner and terms: as for the AuScope logos above.

## Assumption

AuScope has authorised use of these logos in this public package. This has not been
confirmed; confirm with AuScope (also recorded in ADR-023).

## Not included

- **Calibre fonts** (used by the reference repositories): a commercial Klim Type
  Foundry typeface. No redistribution licence was found, so the fonts are not
  shipped. The `--auscope-font-family-base` token uses a system font stack;
  consumers holding a Calibre web licence can add `@font-face` in their own bundle.
- **NCRIS logos**: used only in the footer (Issue #3) and subject to Australian
  Government branding rules.
- **Homepage hero photos**: repository-specific homepage content (0.9 MB and 1.3 MB)
  with unknown photo credit.

## CSS and JavaScript provenance

Everything under `assets/` (the CSS in `assets/css/`, the placeholder
`assets/js/auscope_core.js` and `assets/webassets.yml`) is newly written for this
package. Only colour values and design conventions were taken from the reference
`shared_style.css`; no rules or code were copied.
