# Structure

```
ckanext/auscope_core/
├── plugin.py      # AuscopeCorePlugin; registers templates, public, assets
├── templates/     # Shared Jinja templates and snippets; base.html (only core override)
├── public/auscope_core/  # Served at /auscope_core/: images/ (logos, favicon),
│                         # ASSETS-LICENSES.md
├── assets/        # Webassets library "auscope_core": webassets.yml, js/,
│                  # css/{tokens,base,components,branding}.css
├── i18n/          # Translation catalogues
└── tests/         # pytest tests (test_<module>.py)
docker/            # Dev image, test-env.sh (test connection wrapper), PostgreSQL init
docs/              # architecture.md, decisions.md, branding-analysis.md, design-baseline.md
```

Where new things go:
- Reusable snippets: `templates/snippets/auscope_core/<name>.html` (namespaced to
  avoid clashes with core and consumer templates).
- Core template overrides: same relative path as the core template, using
  `{% ckan_extends %}`. Keep them rare.
- CSS/JS: `assets/css/`, `assets/js/`, plus a bundle entry in `assets/webassets.yml`.
  New brand values go in `tokens.css`; CKAN component recolouring in `branding.css`.
- Static brand files: `public/auscope_core/images/` with an `ASSETS-LICENSES.md` entry.
- Tests: `ckanext/auscope_core/tests/test_<module>.py`.

Design details: docs/architecture.md.
