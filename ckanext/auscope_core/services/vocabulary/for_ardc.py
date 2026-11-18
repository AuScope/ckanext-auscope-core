"""ANZSRC 2020 Fields of Research client for the ARDC LDA service."""

import re

import requests

from ckanext.auscope_core.services.vocabulary.base import (
    MAX_RESPONSE_BYTES,
    InvalidVocabularyInput,
    VocabularyEntry,
    VocabularyNotFound,
    VocabularyProviderError,
    VocabularyResponseError,
    get_json,
    validate_client_configuration,
    validate_limit,
    validate_query,
)

DEFAULT_BASE_URL = (
    "https://vocabs.ardc.edu.au/repository/api/lda/anzsrc-2020-for"
)
DEFAULT_CONCEPT_BASE_URI = "https://linked.data.gov.au/def/anzsrc-for/2020"
VOCABULARY = "ANZSRC 2020 Fields of Research"
_IDENTIFIER_PATTERN = re.compile(r"(?:\d{2}|\d{4}|\d{6})")


class ForVocabularyClient:
    """Search and resolve versioned ANZSRC 2020 FOR concepts."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        concept_base_uri: str = DEFAULT_CONCEPT_BASE_URI,
        connect_timeout: int = 3,
        read_timeout: int = 10,
        default_limit: int = 20,
        max_limit: int = 50,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
        http_get=requests.get,
    ) -> None:
        validate_client_configuration(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            default_limit=default_limit,
            max_limit=max_limit,
            max_response_bytes=max_response_bytes,
            urls={
                "base_url": base_url,
                "concept_base_uri": concept_base_uri,
            },
        )
        self.base_url = base_url.rstrip("/")
        self.concept_base_uri = concept_base_uri.rstrip("/")
        self.timeout = (connect_timeout, read_timeout)
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.max_response_bytes = max_response_bytes
        self.http_get = http_get

    def search(
        self, query: str, *, limit: int | str | None = None
    ) -> list[VocabularyEntry]:
        """Search labels, or resolve an exact two/four/six-digit FOR code."""
        query = validate_query(query)
        limit = validate_limit(limit, self.default_limit, self.max_limit)
        if _IDENTIFIER_PATTERN.fullmatch(query):
            try:
                return [self.lookup(query)]
            except VocabularyNotFound:
                return []

        data = get_json(
            self.http_get,
            f"{self.base_url}/concept.json",
            params={"_page": 0, "_pageSize": limit, "labelcontains": query},
            timeout=self.timeout,
            max_response_bytes=self.max_response_bytes,
        )
        result = data.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("items"), list):
            raise VocabularyResponseError("FOR response is missing result items")
        entries = [self._normalize(item) for item in result["items"]]
        return entries[:limit]

    def lookup(self, identifier: str) -> VocabularyEntry:
        """Resolve an exact ANZSRC 2020 FOR code."""
        identifier = self._normalize_identifier(identifier)
        try:
            data = get_json(
                self.http_get,
                f"{self.base_url}/resource.json",
                params={"uri": f"{self.concept_base_uri}/{identifier}"},
                timeout=self.timeout,
                max_response_bytes=self.max_response_bytes,
            )
        except VocabularyProviderError as error:
            if error.status_code == 404:
                raise VocabularyNotFound(
                    f"FOR identifier {identifier} was not found"
                ) from error
            raise
        result = data.get("result")
        primary = result.get("primaryTopic") if isinstance(result, dict) else None
        if not isinstance(primary, dict) or not primary:
            raise VocabularyResponseError(
                "FOR lookup response is missing primaryTopic"
            )
        entry = self._normalize(primary)
        if entry.id != identifier:
            raise VocabularyResponseError("FOR lookup returned a different identifier")
        return entry

    @staticmethod
    def _normalize_identifier(identifier: object) -> str:
        if not isinstance(identifier, str):
            raise InvalidVocabularyInput("FOR identifier must be a string")
        identifier = identifier.strip()
        if not _IDENTIFIER_PATTERN.fullmatch(identifier):
            raise InvalidVocabularyInput(
                "FOR identifier must contain exactly 2, 4 or 6 digits"
            )
        return identifier

    @staticmethod
    def _normalize(item: object) -> VocabularyEntry:
        if not isinstance(item, dict):
            raise VocabularyResponseError("FOR item must be a JSON object")
        identifier = item.get("notation")
        label_data = item.get("prefLabel")
        label = label_data.get("_value") if isinstance(label_data, dict) else label_data
        if not isinstance(identifier, str) or not _IDENTIFIER_PATTERN.fullmatch(
            identifier
        ):
            raise VocabularyResponseError("FOR item has an invalid notation")
        if not isinstance(label, str) or not label.strip():
            raise VocabularyResponseError("FOR item has an invalid preferred label")
        description = item.get("definition")
        if description is not None and not isinstance(description, str):
            raise VocabularyResponseError("FOR item has an invalid definition")
        return VocabularyEntry(
            id=identifier,
            label=label.strip(),
            description=description.strip() if description else None,
            vocabulary=VOCABULARY,
        )
