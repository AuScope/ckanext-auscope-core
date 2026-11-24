"""Resolve opt-in form sections without changing field definitions."""

import re
from collections.abc import Mapping

_SECTION_ID = re.compile(r"[a-z][a-z0-9-]*")


def _field_names(section, key, known):
    names = section.get(key, [])
    if not isinstance(names, list) or any(
        not isinstance(name, str) or name not in known for name in names
    ):
        raise ValueError(f"Invalid {key} in form section {section['id']!r}")
    if len(names) != len(set(names)):
        raise ValueError(f"Duplicate {key} in form section {section['id']!r}")
    return names


def form_groups(all_fields, active_fields, sections=(), errors=None):
    """Return visible groups for a form page, using full-schema validation."""
    known = {field["field_name"]: field for field in all_fields}
    active = {
        field["field_name"]: field
        for field in active_fields
        if field.get("form_snippet", "") is not None
    }
    if not isinstance(sections, (list, tuple)):
        raise ValueError("Form sections must be an ordered list")

    groups = {}
    membership = {}
    aliases = {}
    for section in sections:
        if not isinstance(section, Mapping):
            raise ValueError("Each form section must be a mapping")
        group_id = section.get("id")
        if (
            not isinstance(group_id, str)
            or not _SECTION_ID.fullmatch(group_id)
            or group_id.startswith("legacy-")
            or group_id in groups
        ):
            raise ValueError(f"Invalid or duplicate form section ID {group_id!r}")
        if not isinstance(section.get("expanded", True), bool):
            raise ValueError(f"Invalid expansion state in form section {group_id!r}")
        groups[group_id] = {
            "id": group_id,
            "heading": section.get("heading", group_id),
            "description": section.get("description"),
            "expanded": section.get("expanded", True),
            "fields": [],
        }
        aliases[group_id] = _field_names(section, "error_fields", known)
        for name in _field_names(section, "fields", known):
            if name in membership or known[name].get("form_snippet", "") is None:
                raise ValueError(f"Duplicate or unrendered form field {name!r}")
            membership[name] = group_id
            if name in active:
                groups[group_id]["fields"].append(active[name])

    field_groups = {}
    legacy_headings = {}
    for name, field in known.items():
        label = field.get("groupBy")
        if label is not None and not isinstance(label, str):
            raise ValueError(f"Invalid groupBy for form field {name!r}")
        if label:
            group_id = label if label in groups else (
                "legacy-" + re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
            )
            if name in membership and membership[name] != group_id:
                raise ValueError(f"Conflicting form section assignments for {name!r}")
            if group_id == "legacy-":
                raise ValueError(
                    f"groupBy for {name!r} requires an explicit section ID"
                )
            field_groups[name] = (group_id, label)
            if group_id.startswith("legacy-"):
                previous = legacy_headings.setdefault(group_id, label)
                if previous != label:
                    raise ValueError(
                        f"Conflicting groupBy labels for section {group_id!r}"
                    )

    for name, field in active.items():
        if name in membership:
            continue
        group_id, label = field_groups.get(name, (None, None))
        group = groups.setdefault(group_id, {
            "id": group_id, "heading": label, "description": None,
            "expanded": True, "fields": [],
        })
        group["fields"].append(field)

    error_names = set()
    for name, value in (errors or {}).items():
        if value and isinstance(name, str):
            error_names.add(
                name if name in known
                else re.split(r"-[0-9]+(?:-|$)", name, maxsplit=1)[0]
            )
    result = []
    for group_id, group in groups.items():
        if not group["fields"]:
            continue
        if group_id is not None:
            names = {field["field_name"] for field in group["fields"]}
            names.update(aliases.get(group_id, ()))
            group["expanded"] = group["expanded"] or bool(names & error_names)
        result.append(group)
    return result
