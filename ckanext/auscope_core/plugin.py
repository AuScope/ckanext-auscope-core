"""CKAN plugin for shared AuScope frontend components."""
import logging

from ckan.common import CKANConfig
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

CKAN_DEFAULT_SITE_LOGO = "/base/images/ckan-logo.png"
CKAN_DEFAULT_FAVICON = "/base/images/ckan.ico"
AUSCOPE_SITE_LOGO = "/auscope_core/images/auscope-logo-icon.png"
AUSCOPE_FAVICON = "/auscope_core/images/auscope-favicon.png"


def _apply_default(config_, key, ckan_default, auscope_default):
    """Replace ``key`` with the AuScope default only if it holds CKAN's default.

    CKAN fills in its defaults before plugins run, and CKAN-generated configs set
    them explicitly, so the value is compared rather than checking whether the key
    is set. Any other value, including an empty string, is kept.
    """
    if config_.get(key) == ckan_default:
        config_[key] = auscope_default
        log.debug("Using AuScope default %s = %s", key, auscope_default)


class AuscopeCorePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # IConfigurer
    def update_config(self, config_: CKANConfig) -> None:
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "auscope_core")
        _apply_default(
            config_, "ckan.site_logo", CKAN_DEFAULT_SITE_LOGO, AUSCOPE_SITE_LOGO
        )
        _apply_default(config_, "ckan.favicon", CKAN_DEFAULT_FAVICON, AUSCOPE_FAVICON)
