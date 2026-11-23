"""Test the ROR API with a mocked upstream HTTP transport."""

import json
from types import SimpleNamespace

import pytest
import requests

from ckanext.auscope_core.services.vocabulary import ror

pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "auscope_core"),
    pytest.mark.usefixtures("with_plugins"),
]
API = "/api/auscope-core/v1/vocabularies/ror"
ID = "https://ror.org/01nfmeh72"
SECOND_ID = "https://ror.org/01sf06y89"


def record(identifier=ID, status="active"):
    return {
        "id": identifier,
        "status": status,
        "names": [
            {"value": "Example Acronym", "types": ["acronym"]},
            {"value": "Example University", "types": ["ror_display"]},
        ],
        "locations": [{"geonames_details": {"country_name": "Australia"}}],
        "relationships": [{"id": SECOND_ID, "type": "parent"}],
    }


@pytest.fixture
def upstream(monkeypatch):
    calls = []

    def install(payload, status=200):
        def get(url, **kwargs):
            calls.append((url, kwargs))
            if isinstance(payload, Exception):
                raise payload
            response = requests.Response()
            response.status_code = status
            response._content = json.dumps(payload).encode()
            response._content_consumed = True
            return response

        monkeypatch.setattr(ror, "requests", SimpleNamespace(get=get))
        return calls

    return install


def test_search_normalizes_active_records_without_resolving_parents(app, upstream):
    calls = upstream({"items": [record(), record(SECOND_ID, "withdrawn")]})
    response = app.get(API, query_string={"q": "Example University", "limit": "1"})
    assert response.status_code == 200
    assert response.json["items"] == [{
        "id": ID, "label": "Example University", "description": "Australia",
        "status": "active", "vocabulary": "Research Organization Registry",
    }]
    assert len(calls) == 1
    url, options = calls[0]
    assert url == ror.DEFAULT_BASE_URL
    assert options["params"] == {"query": "Example University"}
    assert options["timeout"] == (3, 10)
    assert options["stream"] is True
    assert options["allow_redirects"] is False


def test_search_escapes_special_characters_in_organisation_names(app, upstream):
    calls = upstream({"items": [record()]})
    assert app.get(API, query_string={"q": "Centre A/B (Research)"}).status_code == 200
    assert calls[0][1]["params"] == {"query": r"Centre A\/B \(Research\)"}


@pytest.mark.parametrize("status", ["active", "inactive", "withdrawn"])
def test_exact_lookup_returns_registry_status(app, upstream, status):
    calls = upstream(record(status=status))
    response = app.get(f"{API}/lookup", query_string={"id": ID})
    assert response.status_code == 200
    assert response.json["item"]["id"] == ID
    assert response.json["item"]["status"] == status
    assert calls[0][0].endswith("/01nfmeh72")
    response = app.get(API, query_string={"q": "ror.org/01nfmeh72"})
    assert len(response.json["items"]) == (1 if status == "active" else 0)


def test_short_id_lookup(app, upstream):
    upstream(record())
    assert app.get(f"{API}/01nfmeh72").json["item"]["id"] == ID


@pytest.mark.parametrize("identifier", [
    "https://another.example/01nfmeh72", "01nfmeh73",
    "https://ror.org/01nfmeh72?query=1", "http://ror.org/01nfmeh72",
])
def test_invalid_lookup_ids_do_not_call_the_provider(app, upstream, identifier):
    calls = upstream(record())
    response = app.get(f"{API}/lookup", query_string={"id": identifier})
    assert response.status_code == 400
    assert not calls


@pytest.mark.parametrize(("payload", "upstream_status", "expected"), [
    ({}, 404, 404),
    ({}, 429, 503),
    ({}, 500, 502),
    (requests.Timeout(), 200, 503),
    (record(SECOND_ID), 200, 502),
    ({"name": "Unexpected"}, 200, 502),
])
def test_lookup_errors(app, upstream, payload, upstream_status, expected):
    upstream(payload, upstream_status)
    assert app.get(f"{API}/01nfmeh72").status_code == expected


def test_response_size_is_bounded(upstream):
    upstream({"items": [record()]})
    with pytest.raises(ror.VocabularyResponseError, match="too large"):
        ror.RorClient(max_response_bytes=64).search("Example")
