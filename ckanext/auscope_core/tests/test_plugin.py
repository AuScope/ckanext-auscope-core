"""Installation and plugin-loading tests for ckanext-auscope-core."""
import importlib.metadata
import os

import pytest
import yaml

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

import ckanext.auscope_core
from ckanext.auscope_core.plugin import AuscopeCorePlugin

PACKAGE_DIR = os.path.dirname(ckanext.auscope_core.__file__)
ASSETS_DIR = os.path.join(PACKAGE_DIR, "assets")


def _realpath(*parts):
    return os.path.realpath(os.path.join(PACKAGE_DIR, *parts))


def test_entry_point_registered():
    entry_points = list(
        importlib.metadata.entry_points(group="ckan.plugins", name="auscope_core")
    )
    assert len(entry_points) == 1
    assert entry_points[0].load() is AuscopeCorePlugin


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins")
def test_plugin_loaded():
    assert plugins.plugin_loaded("auscope_core")


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins")
def test_template_directory_registered():
    template_paths = [
        os.path.realpath(p) for p in tk.config["computed_template_paths"]
    ]
    assert _realpath("templates") in template_paths


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins")
def test_public_directory_registered():
    # CKAN 2.12 keeps plugin public dirs in "plugin_public_paths" (a list);
    # "extra_public_paths" holds only the user-configured value.
    public_paths = [os.path.realpath(p) for p in tk.config["plugin_public_paths"]]
    assert _realpath("public") in public_paths


def test_webassets_bundles_reference_existing_files():
    with open(os.path.join(ASSETS_DIR, "webassets.yml")) as f:
        bundles = yaml.safe_load(f)

    assert set(bundles) == {"auscope_core-css", "auscope_core-js"}
    for bundle in bundles.values():
        assert bundle["output"].startswith("ckanext-auscope_core/")
        for path in bundle["contents"]:
            assert os.path.isfile(os.path.join(ASSETS_DIR, path))


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_status_show_lists_plugin(app):
    resp = app.get("/api/3/action/status_show")
    assert resp.status_code == 200
    assert "auscope_core" in resp.json["result"]["extensions"]


@pytest.mark.ckan_config("ckan.plugins", "auscope_core")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_home_page_renders(app):
    resp = app.get("/")
    assert resp.status_code == 200
