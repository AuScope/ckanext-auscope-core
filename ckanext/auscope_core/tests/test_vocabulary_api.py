"""Integration tests for the namespaced vocabulary HTTP API."""

import pytest

from ckanext.auscope_core.services.vocabulary import (
    VocabularyEntry,
    VocabularyNotFound,
    VocabularyProviderError,
    VocabularyResponseError,
)


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "auscope_core"),
    pytest.mark.usefixtures("with_plugins"),
]


class FakeClient:
    def search(self, query, *, limit=None):
        return [
            VocabularyEntry(
                id="3705",
                label="Geology",
                vocabulary="ANZSRC 2020 Fields of Research",
            )
        ]

    def lookup(self, identifier):
        return VocabularyEntry(
            id="4326",
            label="WGS 84",
            vocabulary="EPSG Coordinate Reference System",
        )


def test_namespaced_search_api(app, monkeypatch):
    monkeypatch.setattr(
        "ckanext.auscope_core.views.vocabulary.get_vocabulary_client",
        lambda provider: FakeClient(),
    )

    response = app.get("/api/auscope-core/v1/vocabularies/for?q=geology")

    assert response.status_code == 200
    assert response.json == {
        "items": [
            {
                "id": "3705",
                "label": "Geology",
                "vocabulary": "ANZSRC 2020 Fields of Research",
            }
        ]
    }


def test_namespaced_lookup_api(app, monkeypatch):
    monkeypatch.setattr(
        "ckanext.auscope_core.views.vocabulary.get_vocabulary_client",
        lambda provider: FakeClient(),
    )

    response = app.get("/api/auscope-core/v1/vocabularies/epsg/EPSG:4326")

    assert response.status_code == 200
    assert response.json["item"]["id"] == "4326"


def test_malformed_for_lookup_response_maps_to_502(app, monkeypatch):
    class MalformedForClient:
        def lookup(self, identifier):
            raise VocabularyResponseError(
                "FOR lookup response is missing primaryTopic"
            )

    monkeypatch.setattr(
        "ckanext.auscope_core.views.vocabulary.get_vocabulary_client",
        lambda provider: MalformedForClient(),
    )

    response = app.get("/api/auscope-core/v1/vocabularies/for/3705")

    assert response.status_code == 502
    assert response.json["error"]["code"] == "invalid_provider_response"
    assert "primaryTopic" not in response.json["error"]["message"]


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (VocabularyNotFound("not found"), 404, "not_found"),
        (VocabularyProviderError("offline"), 503, "provider_unavailable"),
        (
            VocabularyProviderError("bad gateway", status_code=500),
            502,
            "provider_error",
        ),
        (
            VocabularyResponseError("provider fields changed"),
            502,
            "invalid_provider_response",
        ),
    ],
)
def test_api_maps_service_errors_without_internal_details(
    app, monkeypatch, error, status, code
):
    class BrokenClient:
        def search(self, query, *, limit=None):
            raise error

    monkeypatch.setattr(
        "ckanext.auscope_core.views.vocabulary.get_vocabulary_client",
        lambda provider: BrokenClient(),
    )

    response = app.get("/api/auscope-core/v1/vocabularies/for?q=geology")

    assert response.status_code == status
    assert response.json["error"]["code"] == code
    if status >= 500:
        assert str(error) not in response.json["error"]["message"]


def test_api_rejects_missing_query(app):
    response = app.get("/api/auscope-core/v1/vocabularies/for")

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_input"


def test_api_rejects_limit_above_configured_maximum(app):
    response = app.get(
        "/api/auscope-core/v1/vocabularies/epsg?q=Australian&limit=51"
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_input"


def test_api_rejects_unknown_provider(app):
    response = app.get("/api/auscope-core/v1/vocabularies/gcmd?q=ocean")

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_input"
