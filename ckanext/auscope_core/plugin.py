"""CKAN plugin for shared AuScope components and services."""
import logging

from ckan.common import CKANConfig
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.auscope_core.services.vocabulary.epsg import (
    DEFAULT_BASE_URL as DEFAULT_EPSG_BASE_URL,
)
from ckanext.auscope_core.services.vocabulary.base import (
    MAX_RESPONSE_BYTES,
    validate_client_configuration,
)
from ckanext.auscope_core.services.vocabulary.for_ardc import (
    DEFAULT_BASE_URL as DEFAULT_FOR_BASE_URL,
    DEFAULT_CONCEPT_BASE_URI,
)
from ckanext.auscope_core.services.vocabulary.ror import (
    DEFAULT_BASE_URL as DEFAULT_ROR_BASE_URL,
)
from ckanext.auscope_core.views.vocabulary import blueprint as vocabulary_blueprint

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
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigDeclaration)
    plugins.implements(plugins.IConfigurable)

    # IConfigurer
    def update_config(self, config_: CKANConfig) -> None:
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "auscope_core")
        _apply_default(
            config_, "ckan.site_logo", CKAN_DEFAULT_SITE_LOGO, AUSCOPE_SITE_LOGO
        )
        _apply_default(config_, "ckan.favicon", CKAN_DEFAULT_FAVICON, AUSCOPE_FAVICON)

    # IBlueprint
    def get_blueprint(self):
        return vocabulary_blueprint

    # IConfigurable
    def configure(self, config_: CKANConfig) -> None:
        prefix = "ckanext.auscope_core.vocabulary"
        common = {
            "connect_timeout": config_[f"{prefix}.connect_timeout_seconds"],
            "read_timeout": config_[f"{prefix}.read_timeout_seconds"],
            "default_limit": config_[f"{prefix}.default_limit"],
            "max_limit": config_[f"{prefix}.max_limit"],
            "max_response_bytes": config_[f"{prefix}.max_response_bytes"],
        }
        validate_client_configuration(
            urls={
                "for.base_url": config_[f"{prefix}.for.base_url"],
                "for.concept_base_uri": config_[
                    f"{prefix}.for.concept_base_uri"
                ],
            },
            **common,
        )
        validate_client_configuration(
            urls={
                "epsg.base_url": config_[f"{prefix}.epsg.base_url"],
                "ror.base_url": config_[f"{prefix}.ror.base_url"],
            },
            **common,
        )

    # IConfigDeclaration
    def declare_config_options(self, declaration, key) -> None:
        prefix = "ckanext.auscope_core.vocabulary"
        integer_options = {
            f"{prefix}.connect_timeout_seconds": 3,
            f"{prefix}.read_timeout_seconds": 10,
            f"{prefix}.default_limit": 20,
            f"{prefix}.max_limit": 50,
            f"{prefix}.max_response_bytes": MAX_RESPONSE_BYTES,
        }
        for name, default in integer_options.items():
            declaration.declare(name, default).set_validators("not_empty convert_int")

        declaration.declare(
            f"{prefix}.for.base_url", DEFAULT_FOR_BASE_URL
        ).set_validators("not_empty")
        declaration.declare(
            f"{prefix}.for.concept_base_uri", DEFAULT_CONCEPT_BASE_URI
        ).set_validators("not_empty")
        declaration.declare(
            f"{prefix}.epsg.base_url", DEFAULT_EPSG_BASE_URL
        ).set_validators("not_empty")
        declaration.declare(
            f"{prefix}.ror.base_url", DEFAULT_ROR_BASE_URL
        ).set_validators("not_empty")
