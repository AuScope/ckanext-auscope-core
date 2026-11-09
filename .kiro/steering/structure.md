# Structure

```
ckanext/auscope_core/
├── plugin.py      # AuscopeCorePlugin; registers templates, public, assets
├── templates/     # Shared Jinja templates and snippets
├── public/        # Static files served as-is (images, fonts)
├── assets/        # Webassets library "auscope_core" (webassets.yml, css/, js/)
├── i18n/          # Translation catalogues
└── tests/         # pytest tests (test_<module>.py)
docker/            # Dev image and PostgreSQL init script
docs/              # architecture.md, decisions.md
```

Where new things go:
- Reusable snippets: `templates/snippets/auscope_core/<name>.html` (namespaced to
  avoid clashes with core and consumer templates).
- Core template overrides: same relative path as the core template, using
  `{% ckan_extends %}`. Keep them rare.
- CSS/JS: `assets/css/`, `assets/js/`, plus a bundle entry in `assets/webassets.yml`.
- Tests: `ckanext/auscope_core/tests/test_<module>.py`.

Design details: docs/architecture.md.
