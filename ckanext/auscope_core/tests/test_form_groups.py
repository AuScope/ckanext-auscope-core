"""Tests for the shared presentation-only grouping contract."""

import pytest

from ckanext.auscope_core.form_groups import form_groups


FIELDS = [
    {"field_name": "title", "groupBy": "About Dataset"},
    {"field_name": "description", "groupBy": "About Dataset"},
    {"field_name": "owner_org"},
    {"field_name": "people", "groupBy": "people"},
    {"field_name": "companion", "form_snippet": None},
    {"field_name": "other_page"},
]
SECTIONS = [
    {"id": "people", "heading": "People", "description": "Add participants.",
     "expanded": False, "error_fields": ["companion"]},
    {"id": "empty", "fields": ["other_page"]},
]


def test_effective_page_fields_use_deterministic_section_order():
    active = [FIELDS[i] for i in (1, 0, 2, 3, 4)]
    groups = form_groups(FIELDS, active, SECTIONS)
    assert [group["id"] for group in groups] == ["people", "legacy-about-dataset", None]
    assert [group["fields"] for group in groups] == [
        [FIELDS[3]], active[:2], [FIELDS[2]],
    ]
    assert groups[0]["description"] == "Add participants."
    assert [group["expanded"] for group in groups] == [False, True, True]
    assert groups[1]["heading"] == "About Dataset"


def test_explicit_field_order():
    fields = [{"field_name": "title"}, {"field_name": "description"}]
    sections = [{"id": "about", "fields": ["description", "title"]}]
    assert form_groups(fields, fields, sections)[0]["fields"] == fields[::-1]


@pytest.mark.parametrize("errors", [
    {"people": ["Invalid row"]},
    {"people-2-role": ["Select a role"]},
    {"companion": ["Enter a value"]},
])
def test_group_opens_for_field_row_or_companion_errors(errors):
    assert form_groups(FIELDS, FIELDS, SECTIONS, errors)[0]["expanded"]


def test_error_in_another_group_leaves_closed_section_closed():
    groups = form_groups(FIELDS, FIELDS, SECTIONS, {"title": ["Required"]})
    assert not groups[0]["expanded"]


@pytest.mark.parametrize("sections, message", [
    ([{"id": "a"}, {"id": "a"}], "duplicate form section ID"),
    ([{"id": "Invalid ID"}], "Invalid or duplicate form section ID"),
    ([{"id": "a", "fields": ["unknown"]}], "Invalid fields"),
    ([{"id": "a", "fields": ["title", "title"]}], "Duplicate fields"),
    ([{"id": "a", "fields": ["owner_org"]}, {"id": "b", "fields": ["owner_org"]}],
     "Duplicate or unrendered form field"),
    ([{"id": "a", "fields": ["title"]}], "Conflicting form section assignments"),
    ([{"id": "a", "fields": ["companion"]}], "Duplicate or unrendered form field"),
    ([{"id": "a", "expanded": "false"}], "Invalid expansion state"),
    ([{"id": "a", "error_fields": ["unknown"]}], "Invalid error_fields"),
])
def test_invalid_configuration_is_rejected_even_on_another_page(sections, message):
    with pytest.raises(ValueError, match=message):
        form_groups(FIELDS, [], sections)
