"""Integration tests for the shared header, footer and page layouts."""
import pathlib

import pytest
from bs4 import BeautifulSoup

from ckan.tests import factories

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"


def _soup(app, url, status=200, **kwargs):
    response = app.get(url, status=status, **kwargs)
    assert response.status_code == status, url
    return BeautifulSoup(response.body, "html.parser")


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_header_and_footer_render_on_common_pages(app):
    dataset = factories.Dataset(type="dataset")
    for url in ("/", "/dataset", f"/dataset/{dataset['name']}", "/user/login"):
        soup = _soup(app, url)
        assert soup.select_one("header.masthead .auscope-header-brand")
        assert soup.select_one("nav.account[aria-label='Account']")
        assert soup.select_one("footer.site-footer")
        headings = {
            heading.get_text(" ", strip=True)
            for heading in soup.select("footer.site-footer h2")
        }
        assert headings == {"Contact Us", "Funding", "Community"}
        assert soup.select_one(".auscope-footer__main address")
        assert soup.select_one(".auscope-footer__social-links")
        acknowledgement = soup.select_one(".auscope-footer__acknowledgement")
        assert "past, present and emerging" in acknowledgement.get_text(" ", strip=True)


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_homepage_uses_full_width_search_and_two_column_content(app):
    soup = _soup(app, "/")
    hero = soup.select_one(".homepage .hero")
    assert hero.select_one(":scope > .container > .module-search")
    columns = soup.select(".homepage .module-feeds .row > .col-md-6")
    assert len(columns) == 2


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_ckan_page_variants_keep_content_before_direct_body_footer(app):
    dataset = factories.Dataset(type="dataset")
    organization = factories.Organization()
    pages = (
        ("/", 200),
        ("/dataset", 200),
        (f"/dataset/{dataset['name']}", 200),
        ("/organization", 200),
        (f"/organization/{organization['name']}", 200),
        ("/user/login", 200),
        ("/auscope-core-layout-missing-page", 404),
    )

    for url, status in pages:
        body = _soup(app, url, status=status).body
        direct_children = body.find_all(recursive=False)
        footer = body.select_one(":scope > footer.site-footer")
        content = next(
            (
                child
                for child in direct_children
                if "main" in child.get("class", [])
                or "homepage" in child.get("class", [])
                or child.get("role") == "main"
            ),
            None,
        )
        assert content is not None, url
        assert footer is not None, url
        assert direct_children.index(content) < direct_children.index(footer), url


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.ckan_config("ckan.auth.create_unowned_dataset", True)
@pytest.mark.ckan_config("ckan.auth.create_dataset_if_not_in_organization", True)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
def test_create_and_edit_forms_use_standard_page_layout(app):
    user = factories.UserWithToken()
    dataset = factories.Dataset(user=user, type="dataset")
    headers = {"Authorization": user["token"]}

    for url in ("/dataset/new", f"/dataset/edit/{dataset['name']}"):
        soup = _soup(app, url, headers=headers)
        assert soup.select_one("body > .main form#dataset-edit"), url
        assert soup.select_one("body > footer.site-footer"), url


def test_templates_expose_consumer_customisation_blocks():
    header = (TEMPLATES_DIR / "header.html").read_text(encoding="utf-8")
    footer = (TEMPLATES_DIR / "footer.html").read_text(encoding="utf-8")
    home = (TEMPLATES_DIR / "home" / "index.html").read_text(encoding="utf-8")

    assert "{% ckan_extends %}" in header
    assert "block auscope_header_brand_mark" in header
    assert "block auscope_header_repository_title" in header
    for name in (
        "contact",
        "funding",
        "funding_branding",
        "community",
        "community_links",
        "social_links",
        "acknowledgement",
        "meta",
    ):
        assert f"block auscope_footer_{name}" in footer
    assert "block footer_attribution" in footer
    assert "block footer_lang" in footer
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
