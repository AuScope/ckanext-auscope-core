"""Read-only, versioned HTTP API for shared vocabularies."""

import logging

from flask import Blueprint, jsonify, request

import ckan.plugins.toolkit as toolkit

from ckanext.auscope_core.services.vocabulary import (
    EpsgVocabularyClient,
    ForVocabularyClient,
    InvalidVocabularyInput,
    VocabularyNotFound,
    VocabularyProviderError,
    VocabularyResponseError,
)

log = logging.getLogger(__name__)

blueprint = Blueprint("auscope_core_vocabulary", __name__)
_PREFIX = "ckanext.auscope_core.vocabulary"


def _config_int(name: str) -> int:
    return int(toolkit.config[f"{_PREFIX}.{name}"])


def get_vocabulary_client(provider: str):
    """Build a configured provider client for one request."""
    common = {
        "connect_timeout": _config_int("connect_timeout_seconds"),
        "read_timeout": _config_int("read_timeout_seconds"),
        "default_limit": _config_int("default_limit"),
        "max_limit": _config_int("max_limit"),
        "max_response_bytes": _config_int("max_response_bytes"),
    }
    if provider == "for":
        return ForVocabularyClient(
            base_url=toolkit.config[f"{_PREFIX}.for.base_url"],
            concept_base_uri=toolkit.config[f"{_PREFIX}.for.concept_base_uri"],
            **common,
        )
    if provider == "epsg":
        return EpsgVocabularyClient(
            base_url=toolkit.config[f"{_PREFIX}.epsg.base_url"],
            **common,
        )
    raise InvalidVocabularyInput("provider must be 'for' or 'epsg'")


def _error(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status


def _handle_error(error: Exception, provider: str):
    if isinstance(error, InvalidVocabularyInput):
        return _error("invalid_input", str(error), 400)
    if isinstance(error, VocabularyNotFound):
        return _error("not_found", str(error), 404)
    if isinstance(error, VocabularyResponseError):
        log.warning("Invalid %s vocabulary provider response: %s", provider, error)
        return _error(
            "invalid_provider_response",
            "The vocabulary provider returned an invalid response.",
            502,
        )
    if isinstance(error, VocabularyProviderError):
        log.warning("%s vocabulary provider request failed: %s", provider, error)
        status = 502 if error.status_code is not None else 503
        code = "provider_error" if status == 502 else "provider_unavailable"
        message = (
            "The vocabulary provider request failed."
            if status == 502
            else "The vocabulary provider is unavailable."
        )
        return _error(code, message, status)
    raise error


@blueprint.get("/api/auscope-core/v1/vocabularies/<provider>")
def vocabulary_search(provider: str):
    """Search a configured FOR or EPSG vocabulary."""
    try:
        client = get_vocabulary_client(provider)
        entries = client.search(request.args.get("q"), limit=request.args.get("limit"))
        return jsonify({"items": [entry.as_dict() for entry in entries]})
    except (
        InvalidVocabularyInput,
        VocabularyNotFound,
        VocabularyProviderError,
        VocabularyResponseError,
    ) as error:
        return _handle_error(error, provider)


@blueprint.get("/api/auscope-core/v1/vocabularies/<provider>/<identifier>")
def vocabulary_lookup(provider: str, identifier: str):
    """Resolve one FOR or EPSG identifier."""
    try:
        client = get_vocabulary_client(provider)
        return jsonify({"item": client.lookup(identifier).as_dict()})
    except (
        InvalidVocabularyInput,
        VocabularyNotFound,
        VocabularyProviderError,
        VocabularyResponseError,
    ) as error:
        return _handle_error(error, provider)
