"""Integration tests for the shared header, footer and page layouts."""
import pathlib

import pytest
from bs4 import BeautifulSoup

from ckan.tests import factories

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"


def _soup(app, url):
    response = app.get(url)
    assert response.status_code == 200, url
    return BeautifulSoup(response.body, "html.parser")


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_header_and_footer_render_on_common_pages(app):
    dataset = factories.Dataset()
    for url in ("/", "/dataset", f"/dataset/{dataset['name']}", "/user/login"):
        soup = _soup(app, url)
        assert soup.select_one("header.masthead .auscope-header-brand")
        assert soup.select_one("nav.account[aria-label='Account']")
        assert soup.select_one("footer.site-footer")
        headings = {
            heading.get_text(" ", strip=True)
            for heading in soup.select("footer.site-footer h2")
        }
        assert headings == {"Contact", "Funding", "Community"}
        assert soup.select_one(".auscope-footer__bottom .attribution")


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_homepage_uses_full_width_search_and_two_column_content(app):
    soup = _soup(app, "/")
    hero = soup.select_one(".homepage .hero")
    assert hero.select_one(":scope > .container > .module-search")
    columns = soup.select(".homepage .module-feeds .row > .col-md-6")
    assert len(columns) == 2


def test_templates_expose_consumer_customisation_blocks():
    header = (TEMPLATES_DIR / "header.html").read_text(encoding="utf-8")
    footer = (TEMPLATES_DIR / "footer.html").read_text(encoding="utf-8")
    home = (TEMPLATES_DIR / "home" / "index.html").read_text(encoding="utf-8")

    assert "{% ckan_extends %}" in header
    assert "block auscope_header_brand_mark" in header
    assert "block auscope_header_repository_title" in header
    for name in ("contact", "funding", "community", "acknowledgement"):
        assert f"block auscope_footer_{name}" in footer
    for name in ("search", "promoted", "featured_group", "featured_organization"):
        assert f"block {name}" in home


def test_reusable_page_section_uses_native_ckan_module_classes():
    macro = (
        TEMPLATES_DIR / "snippets" / "auscope_core" / "page_section.html"
    ).read_text(encoding="utf-8")
    assert "macro page_section" in macro
    assert 'class="module auscope-page-section' in macro
    assert 'class="module-heading"' in macro
    assert 'class="module-content"' in macro
