# Product

Shared CKAN 2.12.1 extension (`ckanext-auscope-core`, plugin `auscope_core`) that
removes duplicated frontend code from the AuScope CKAN repositories.

Consumers:
- Data Repository
- Sample Repository
- Instrument Registry (PIDINST)
- RAiD Repository (in development)

In scope: shared branding, themes, layouts, reusable UI components and common
frontend functionality.

Out of scope: business logic, repository-specific schemas and metadata, CKAN core
changes. These stay in each repository's own extensions.

Current status: shared styling and branding (Issue #2), with shared header, footer
and page layouts in Issue #3. UI components follow in later issues.

Rules: see AGENTS.md.
