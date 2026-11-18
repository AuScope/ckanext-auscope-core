"""Provider-contract tests for shared FOR and EPSG clients."""

import json

import pytest
import requests

from ckanext.auscope_core.services.vocabulary import (
    EpsgVocabularyClient,
    ForVocabularyClient,
    InvalidVocabularyInput,
    VocabularyConfigurationError,
    VocabularyError,
    VocabularyNotFound,
    VocabularyProviderError,
    VocabularyResponseError,
)


class FakeResponse:
    def __init__(
        self, payload=None, *, body=None, chunks=None, status=200, headers=None
    ):
        self.status_code = status
        self.headers = headers or {}
        self.body = json.dumps(payload).encode() if body is None else body
        self.chunks = chunks
        self.closed = False
        self.iterated = False

    def iter_content(self, chunk_size):
        self.iterated = True
        chunks = self.chunks if self.chunks is not None else [self.body]
        for chunk in chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk

    def close(self):
        self.closed = True


class FakeGet:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


FOR_ITEM = {
    "_about": "https://linked.data.gov.au/def/anzsrc-for/2020/3705",
    "notation": "3705",
    "prefLabel": {"_value": "Geology", "_lang": "en"},
    "definition": "This group covers geology.",
}
EPSG_SEARCH_ITEM = {
    "Code": 4326,
    "Name": "WGS 84",
    "Type": "geographic 2D",
    "Remarks": None,
}
EPSG_LOOKUP_ITEM = {
    "Code": 4326,
    "Name": "WGS 84",
    "Kind": "geographic 2D",
    "Remark": "Horizontal component of the WGS 84 system.",
}


def test_for_search_normalizes_provider_response_and_request():
    response = FakeResponse({"result": {"items": [FOR_ITEM]}})
    get = FakeGet(response)

    entries = ForVocabularyClient(http_get=get).search(" geology ", limit=1)

    assert entries[0].as_dict() == {
        "id": "3705",
        "label": "Geology",
        "description": "This group covers geology.",
        "vocabulary": "ANZSRC 2020 Fields of Research",
    }
    url, kwargs = get.calls[0]
    assert url.endswith("/concept.json")
    assert kwargs["params"] == {
        "_page": 0,
        "_pageSize": 1,
        "labelcontains": "geology",
    }
    assert kwargs["timeout"] == (3, 10)
    assert kwargs["stream"] is True
    assert response.closed


def test_for_lookup_uses_versioned_authoritative_uri():
    get = FakeGet(FakeResponse({"result": {"primaryTopic": FOR_ITEM}}))

    entry = ForVocabularyClient(http_get=get).lookup("3705")

    assert entry.id == "3705"
    assert get.calls[0][1]["params"] == {
        "uri": "https://linked.data.gov.au/def/anzsrc-for/2020/3705"
    }


def test_for_exact_code_search_uses_lookup():
    get = FakeGet(FakeResponse({"result": {"primaryTopic": FOR_ITEM}}))

    entries = ForVocabularyClient(http_get=get).search("3705")

    assert [entry.id for entry in entries] == ["3705"]
    assert get.calls[0][0].endswith("/resource.json")


def test_for_empty_search_result():
    get = FakeGet(FakeResponse({"result": {"items": []}}))

    assert ForVocabularyClient(http_get=get).search("no match") == []


@pytest.mark.parametrize("identifier", ["", "3", "370", "37A5", "1234567"])
def test_for_rejects_invalid_identifier(identifier):
    with pytest.raises(InvalidVocabularyInput):
        ForVocabularyClient().lookup(identifier)


def test_for_404_lookup_is_not_found():
    get = FakeGet(FakeResponse({}, status=404))

    with pytest.raises(VocabularyNotFound):
        ForVocabularyClient(http_get=get).lookup("3705")


def test_for_missing_lookup_result_is_malformed_provider_response():
    get = FakeGet(FakeResponse({"result": {}}))

    with pytest.raises(VocabularyResponseError):
        ForVocabularyClient(http_get=get).lookup("3705")


def test_epsg_search_normalizes_codes_as_strings_and_bounds_results():
    second = {**EPSG_SEARCH_ITEM, "Code": 4283, "Name": "GDA94"}
    get = FakeGet(FakeResponse({"Results": [EPSG_SEARCH_ITEM, second]}))

    entries = EpsgVocabularyClient(http_get=get).search("WGS", limit=1)

    assert [entry.as_dict() for entry in entries] == [
        {
            "id": "4326",
            "label": "WGS 84",
            "vocabulary": "EPSG Coordinate Reference System",
        }
    ]
    assert get.calls[0][1]["params"]["pageSize"] == 1
    assert get.calls[0][1]["params"]["includeDeprecated"] == "false"


def test_epsg_lookup_normalizes_prefix_and_description():
    get = FakeGet(FakeResponse(EPSG_LOOKUP_ITEM))

    entry = EpsgVocabularyClient(http_get=get).lookup(" epsg:4326 ")

    assert entry.as_dict() == {
        "id": "4326",
        "label": "WGS 84",
        "description": "Horizontal component of the WGS 84 system.",
        "vocabulary": "EPSG Coordinate Reference System",
    }
    assert get.calls[0][0].endswith("/CoordRefSystem/4326")


def test_epsg_exact_code_search_uses_lookup():
    get = FakeGet(FakeResponse(EPSG_LOOKUP_ITEM))

    assert EpsgVocabularyClient(http_get=get).search("EPSG:4326")[0].id == "4326"


def test_epsg_empty_search_result():
    get = FakeGet(FakeResponse({"Results": []}))

    assert EpsgVocabularyClient(http_get=get).search("no match") == []


@pytest.mark.parametrize("identifier", ["", "EPSG:", "0", "-1", "4326.0", "x"])
def test_epsg_rejects_invalid_identifier(identifier):
    with pytest.raises(InvalidVocabularyInput):
        EpsgVocabularyClient().lookup(identifier)


def test_epsg_404_lookup_is_not_found():
    get = FakeGet(FakeResponse({}, status=404))

    with pytest.raises(VocabularyNotFound):
        EpsgVocabularyClient(http_get=get).lookup("4326")


@pytest.mark.parametrize(
    ("client", "payload", "identifier"),
    [
        (
            ForVocabularyClient,
            {"result": {"primaryTopic": {"notation": "3705"}}},
            "3705",
        ),
        (EpsgVocabularyClient, {}, "4326"),
        (EpsgVocabularyClient, {"Code": 4326}, "4326"),
    ],
)
def test_lookup_rejects_missing_or_malformed_provider_data(
    client, payload, identifier
):
    get = FakeGet(FakeResponse(payload))

    with pytest.raises(VocabularyResponseError):
        client(http_get=get).lookup(identifier)


@pytest.mark.parametrize("query", ["", " ", "x" * 101, None])
def test_search_rejects_invalid_query(query):
    with pytest.raises(InvalidVocabularyInput):
        EpsgVocabularyClient().search(query)


@pytest.mark.parametrize("limit", [0, 51, "many", True])
def test_search_rejects_invalid_limit(limit):
    with pytest.raises(InvalidVocabularyInput):
        ForVocabularyClient().search("geology", limit=limit)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"connect_timeout": 0},
        {"connect_timeout": -1},
        {"connect_timeout": float("inf")},
        {"read_timeout": 0},
        {"read_timeout": float("nan")},
        {"default_limit": 0},
        {"max_limit": 0},
        {"default_limit": 11, "max_limit": 10},
        {"max_response_bytes": 0},
        {"base_url": ""},
        {"base_url": "ftp://example.test/api"},
        {"base_url": "https://example.test/api?query=1"},
    ],
)
def test_client_rejects_invalid_configuration(kwargs):
    with pytest.raises(VocabularyConfigurationError):
        EpsgVocabularyClient(**kwargs)


def test_for_client_rejects_invalid_concept_base_uri():
    with pytest.raises(VocabularyConfigurationError):
        ForVocabularyClient(concept_base_uri="not-a-url")


def test_client_accepts_positive_boundary_configuration():
    client = EpsgVocabularyClient(
        base_url="http://localhost:5000/api",
        connect_timeout=0.1,
        read_timeout=0.1,
        default_limit=1,
        max_limit=1,
        max_response_bytes=1,
    )

    assert client.timeout == (0.1, 0.1)
    assert client.default_limit == client.max_limit == 1


def test_vocabulary_error_is_part_of_public_api():
    assert issubclass(VocabularyConfigurationError, VocabularyError)
    assert issubclass(VocabularyResponseError, VocabularyError)


@pytest.mark.parametrize(
    ("client", "payload"),
    [
        (ForVocabularyClient, {}),
        (ForVocabularyClient, {"result": {"items": [{"notation": "3705"}]}}),
        (EpsgVocabularyClient, {}),
        (EpsgVocabularyClient, {"Results": [{"Code": 4326}]}),
    ],
)
def test_search_rejects_missing_or_malformed_provider_data(client, payload):
    get = FakeGet(FakeResponse(payload))

    with pytest.raises(VocabularyResponseError):
        client(http_get=get).search("geology")


@pytest.mark.parametrize(
    "response",
    [
        requests.Timeout("timed out"),
        requests.ConnectionError("offline"),
    ],
)
def test_network_failure_and_timeout_are_provider_errors(response):
    get = FakeGet(response)

    with pytest.raises(VocabularyProviderError):
        ForVocabularyClient(http_get=get).search("geology")


def test_streaming_timeout_is_provider_error_and_closes_response():
    response = FakeResponse(chunks=[b'{"Results":', requests.Timeout("timed out")])
    get = FakeGet(response)

    with pytest.raises(VocabularyProviderError):
        EpsgVocabularyClient(http_get=get).search("WGS")

    assert response.closed


def test_upstream_http_failure_is_provider_error():
    get = FakeGet(FakeResponse({}, status=500))

    with pytest.raises(VocabularyProviderError) as error:
        EpsgVocabularyClient(http_get=get).search("WGS")

    assert error.value.status_code == 500


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse([]),
        FakeResponse(body=b"{"),
        FakeResponse({}, headers={"Content-Length": "unknown"}),
        FakeResponse({}, headers={"Content-Length": "-1"}),
    ],
)
def test_unsafe_provider_response_is_rejected(response):
    get = FakeGet(response)

    with pytest.raises(VocabularyResponseError):
        EpsgVocabularyClient(http_get=get).search("WGS")

    assert response.closed


def test_oversized_content_length_is_rejected_before_streaming():
    response = FakeResponse({}, headers={"Content-Length": "1000001"})

    with pytest.raises(VocabularyResponseError, match="too large"):
        EpsgVocabularyClient(http_get=FakeGet(response)).search("WGS")

    assert not response.iterated
    assert response.closed


def test_oversized_stream_without_content_length_stops_and_closes():
    response = FakeResponse(chunks=[b"x" * 1_000_000, b"x"])

    with pytest.raises(VocabularyResponseError, match="too large"):
        EpsgVocabularyClient(http_get=FakeGet(response)).search("WGS")

    assert response.iterated
    assert response.closed


def test_response_at_configured_byte_limit_is_accepted():
    body = b"{}"
    response = FakeResponse(body=body, headers={"Content-Length": str(len(body))})

    with pytest.raises(VocabularyResponseError, match="missing Results"):
        EpsgVocabularyClient(
            http_get=FakeGet(response), max_response_bytes=len(body)
        ).search("WGS")

    assert response.closed
