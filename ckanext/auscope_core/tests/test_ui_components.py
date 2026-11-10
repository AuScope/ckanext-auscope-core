"""Checks for reusable, namespaced UI components."""
import pathlib

import pytest
from bs4 import BeautifulSoup
import ckan.plugins.toolkit as toolkit


PACKAGE_DIR = pathlib.Path(__file__).resolve().parent.parent
FACET_TEMPLATE = "snippets/auscope_core/facet_select.html"


class FacetItem(dict):
    """Mapping with attribute access, matching CKAN's facet item contract."""

    __getattr__ = dict.__getitem__


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins")
def test_facet_select_renders_accessible_native_control(app):
    items = [
        FacetItem(name="geology", display_name="Geology", count=3, active=True),
        FacetItem(name="water", display_name="Water", count=2, active=False),
    ]
    with app.flask_app.test_request_context("/dataset?tags=old&q=rocks&page=2"):
        html = toolkit.render(
            FACET_TEMPLATE,
            extra_vars={"name": "tags", "title": "Keywords", "items": items},
        )

    soup = BeautifulSoup(html, "html.parser")
    section = soup.select_one("section.auscope-core-facet-select")
    control = section.select_one("select.form-select[name='tags'][multiple]")
    label = section.select_one(f"label[for='{control['id']}']")
    assert label.get_text(" ", strip=True) == "Filter by Keywords"
    assert control["aria-describedby"]
    assert section.select_one(f"#{control['aria-describedby']}")
    option_labels = [
        option.get_text(" ", strip=True) for option in control.select("option")
    ]
    assert option_labels == [
        "Geology (3)",
        "Water (2)",
    ]
    assert control.select_one("option[value='geology'][selected]")
    assert section.select_one("button.btn-primary[type='submit']")
    hidden = {(field["name"], field["value"]) for field in section.select("input")}
    assert hidden == {("q", "rocks")}
    assert not section.select("script, style")


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins")
def test_facet_select_empty_and_hidden_states(app):
    with app.flask_app.test_request_context("/dataset"):
        empty = toolkit.render(
            FACET_TEMPLATE,
            extra_vars={"name": "tags", "title": "Keywords", "items": []},
        )
        hidden = toolkit.render(
            FACET_TEMPLATE,
            extra_vars={
                "name": "tags",
                "title": "Keywords",
                "items": [],
                "hide_empty": True,
            },
        )

    assert "There are no Keywords that match this search" in empty
    assert not hidden.strip()


def test_component_template_is_namespaced_and_css_has_no_inline_escape_hatches():
    template = (PACKAGE_DIR / "templates" / FACET_TEMPLATE).read_text(encoding="utf-8")
    css = (PACKAGE_DIR / "assets" / "css" / "components.css").read_text(
        encoding="utf-8"
    )
    assert "auscope-core-facet-select" in template
    assert "<script" not in template
    assert "<style" not in template
    assert "inline-size: 100%" in css
    assert "min-block-size" in css
    assert "!important" not in css
    assert "url(" not in css
