"""CKAN integration tests for the shared theme: bundles, rendering and assets."""
import pytest
from bs4 import BeautifulSoup

import ckan.plugins.toolkit as tk
from ckan.lib.webassets_tools import is_registered

from ckanext.auscope_core.plugin import AUSCOPE_FAVICON, AUSCOPE_SITE_LOGO

IMAGES = [
    "auscope-logo.png",
    "auscope-logo-reversed.png",
    "auscope-logo-icon.png",
    "auscope-favicon.png",
]


def _soup(app, url="/"):
    resp = app.get(url)
    assert resp.status_code == 200
    return BeautifulSoup(resp.body, "html.parser")


def _stylesheets(soup):
    return [link["href"] for link in soup.find_all("link", rel="stylesheet")]


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.parametrize(
    "name", ["auscope_core-tokens", "auscope_core-css", "auscope_core-js"]
)
def test_bundle_registered(name):
    assert is_registered(f"auscope_core/{name}")


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.ckan_config("ckan.webassets.debug", "false")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_stylesheets_load_after_core_and_are_served(app):
    hrefs = _stylesheets(_soup(app))

    def position(suffix):
        matches = [i for i, href in enumerate(hrefs) if href.endswith(suffix)]
        assert len(matches) == 1, (suffix, hrefs)
        return matches[0]

    assert (
        position("main.css")
        < position("-auscope_core-tokens.css")
        < position("-auscope_core.css")
    )

    auscope = [href for href in hrefs if "ckanext-auscope_core/" in href]
    assert len(auscope) == 2
    for href in auscope:
        resp = app.get(href)
        assert resp.status_code == 200, href
    tokens = app.get(hrefs[position("-auscope_core-tokens.css")]).body
    assert "--auscope-color-primary" in tokens


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.parametrize("name", IMAGES)
def test_branding_image_served(app, name):
    resp = app.get(f"/auscope_core/images/{name}")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "image/png"


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_asset_licences_served(app):
    resp = app.get("/auscope_core/ASSETS-LICENSES.md")
    assert resp.status_code == 200


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.ckan_config("ckan.site_logo", "/base/images/ckan-logo.png")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_default_logo_and_favicon_replaced(app):
    assert tk.config["ckan.site_logo"] == AUSCOPE_SITE_LOGO
    assert tk.config["ckan.favicon"] == AUSCOPE_FAVICON
    html = app.get("/").body
    assert f'src="{AUSCOPE_SITE_LOGO}"' in html
    assert f'href="{AUSCOPE_FAVICON}"' in html


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_explicit_logo_from_test_config_kept(app):
    # test-core.ini sets ckan.site_logo to a non-default path and leaves the
    # favicon at CKAN's default.
    logo = "/images/ckan_logo_fullname_long.png"
    assert tk.config["ckan.site_logo"] == logo
    assert tk.config["ckan.favicon"] == AUSCOPE_FAVICON
    html = app.get("/").body
    assert f'src="{logo}"' in html
    assert f'href="{AUSCOPE_FAVICON}"' in html


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.ckan_config("ckan.site_logo", "/custom/logo.png")
@pytest.mark.ckan_config("ckan.favicon", "/custom/fav.ico")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_custom_logo_and_favicon_kept(app):
    assert tk.config["ckan.site_logo"] == "/custom/logo.png"
    assert tk.config["ckan.favicon"] == "/custom/fav.ico"
    html = app.get("/").body
    assert 'src="/custom/logo.png"' in html
    assert 'href="/custom/fav.ico"' in html


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.ckan_config("ckan.site_logo", "")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_empty_logo_shows_text_title(app):
    soup = _soup(app)
    assert soup.select(".masthead .logo img") == []
    titles = [
        title.get_text(strip=True)
        for title in soup.select(".masthead .auscope-header-brand__title")
    ]
    assert tk.config["ckan.site_title"] in titles


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_homepage_search_headings_rendered(app):
    soup = _soup(app)
    headings = [
        h.get_text(strip=True)
        for h in soup.select(".module-search h1, .module-search h2, .module-search h3")
    ]
    assert "Search data" in headings
    assert "Popular tags" in headings


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.ckan_config("ckan.site_title", "AuScope RAiD Repository")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_repository_title_uses_native_site_title(app):
    soup = _soup(app)
    brand = soup.select_one(".auscope-header-brand")
    assert brand.get_text(" ", strip=True) == "AuScope RAiD Repository"
    assert brand["href"] == "/"
    assert brand.select_one("img")["alt"] == ""
