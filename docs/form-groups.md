# Shared dataset form groups

Consumer extensions can group the fields on a Scheming create or edit form by
calling `h.auscope_core_form_groups(all_fields, active_fields, sections, errors)`
from their existing form template. Core adds a helper, a namespaced macro and
opt-in assets. The consumer selects the active page and renders its fields
through the same snippet and context as its installed Scheming version.

## Configuration

The consumer may store an ordered list as `form_groups` alongside its dataset
schema and pass that value as `sections`. For example:

```yaml
form_groups:
  - id: about
    heading: About the dataset
    description: Describe the dataset and its purpose.
    fields: [title, notes]
  - id: access
    heading: Access
    expanded: false
    fields: [access_type]
    error_fields: [embargo_expiry]
```

- `id` is unique within the configuration and uses lowercase ASCII letters,
  digits and hyphens, starting with a letter. `legacy-` is reserved.
- `heading` defaults to the ID. `description` is optional. Consumers resolve
  localized values before passing text to the macro. The macro escapes this text.
- `fields` sets membership and explicit order. Fields assigned through
  `groupBy` alone follow active-page order within their section.
- `expanded` defaults to true. An error on a rendered field, a numbered
  subfield, or an `error_fields` alias opens its section on redisplay.
  Use aliases when one field's snippet renders companion controls.
- The configured sections come first in list order. Implicit groups and the
  ungrouped block follow in first-occurrence order on the active page. Gathering
  fields into one section can bring non-contiguous fields together, while each
  group's own field order is preserved. Omitted and empty sections create no
  markup. Fields with `form_snippet: null` are skipped, and ungrouped fields
  remain visible. Invalid IDs, unknown field names, duplicate assignments and
  conflicting grouping declarations raise a configuration error. Validation
  uses all dataset fields so references to another page remain valid.

## Opt in from a consumer

Pass the expanded dataset fields and the current Scheming page's effective
field list. Pass the complete form error mapping. Import the `form_group` macro
from `snippets/auscope_core/form_group.html`, and give each rendered section a
form-specific prefix plus its stable ID. Use the macro to wrap the consumer's
usual field renderer. Render groups with a null ID directly. Wrap this output
with the `auscope-core-form-groups` class and the same CKAN module name, and
include `auscope_core/auscope-core-form-groups-css` and
`auscope_core/auscope-core-form-groups-js` using CKAN's `asset` tag.

Keep the outer form, defaults, validation summaries, phase markers, actions
and values in the existing consumer/Scheming path. Call the original block
when grouping is disabled. The macro uses native `details` and `summary` so
keyboard toggles work independently of JavaScript. The script only reveals
sections on native validation or an in-form anchor click. The existing
`page_section.html` macro remains suitable for static page sections.

## Adopt through legacy groupBy

Opt in and pass an empty section list to use existing `groupBy` labels. The
helper derives stable IDs from those labels and groups in first-occurrence
order. To set a heading, description, or initial expansion explicitly, declare
the section and change its fields' `groupBy` values to the section ID. A
consumer can also remove those tags and provide an ordered `fields` list.
Use explicit IDs if legacy labels cannot produce a unique ASCII ID. Before
switching, check any legacy hidden General controls and initial panel state.
Keep any hidden-but-submitted behavior within the consumer adapter.

RAiD is the first consumer on CKAN 2.12.1 and Scheming 3.1.0. Repeatable fields
and persistence remain the responsibility of the existing field extensions.
Older CKAN versions and consumer-specific widgets such as maps need parity
checks in their own stacks before migration.
