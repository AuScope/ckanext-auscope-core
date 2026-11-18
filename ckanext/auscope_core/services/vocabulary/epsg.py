"""EPSG coordinate reference system vocabulary client."""

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

DEFAULT_BASE_URL = "https://apps.epsg.org/api/v1"
VOCABULARY = "EPSG Coordinate Reference System"
_IDENTIFIER_PATTERN = re.compile(r"(?:EPSG\s*:\s*)?([1-9]\d{0,7})", re.IGNORECASE)


class EpsgVocabularyClient:
    """Search and resolve non-deprecated EPSG CRS codes."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
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
            urls={"base_url": base_url},
        )
        self.base_url = base_url.rstrip("/")
        self.timeout = (connect_timeout, read_timeout)
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.max_response_bytes = max_response_bytes
        self.http_get = http_get

    def search(
        self, query: str, *, limit: int | str | None = None
    ) -> list[VocabularyEntry]:
        """Search CRS names, or resolve an exact numeric/``EPSG:`` code."""
        query = validate_query(query)
        limit = validate_limit(limit, self.default_limit, self.max_limit)
        if _IDENTIFIER_PATTERN.fullmatch(query):
            try:
                return [self.lookup(query)]
            except VocabularyNotFound:
                return []

        data = get_json(
            self.http_get,
            f"{self.base_url}/CoordRefSystem/",
            params={
                "includeDeprecated": "false",
                "pageSize": limit,
                "page": 0,
                "keywords": query,
            },
            timeout=self.timeout,
            max_response_bytes=self.max_response_bytes,
        )
        items = data.get("Results")
        if not isinstance(items, list):
            raise VocabularyResponseError("EPSG response is missing Results")
        entries = [self._normalize(item, lookup=False) for item in items]
        return entries[:limit]

    def lookup(self, identifier: str) -> VocabularyEntry:
        """Resolve a numeric EPSG code, accepting an optional ``EPSG:`` prefix."""
        identifier = self._normalize_identifier(identifier)
        try:
            data = get_json(
                self.http_get,
                f"{self.base_url}/CoordRefSystem/{identifier}",
                params=None,
                timeout=self.timeout,
                max_response_bytes=self.max_response_bytes,
            )
        except VocabularyProviderError as error:
            if error.status_code == 404:
                raise VocabularyNotFound(
                    f"EPSG identifier {identifier} was not found"
                ) from error
            raise
        if not data:
            raise VocabularyResponseError("EPSG lookup response is empty")
        entry = self._normalize(data, lookup=True)
        if entry.id != identifier:
            raise VocabularyResponseError("EPSG lookup returned a different identifier")
        return entry

    @staticmethod
    def _normalize_identifier(identifier: object) -> str:
        if not isinstance(identifier, str):
            raise InvalidVocabularyInput("EPSG identifier must be a string")
        match = _IDENTIFIER_PATTERN.fullmatch(identifier.strip())
        if not match:
            raise InvalidVocabularyInput(
                "EPSG identifier must be a positive numeric code "
                "with an optional prefix"
            )
        return match.group(1)

    @staticmethod
    def _normalize(item: object, *, lookup: bool) -> VocabularyEntry:
        if not isinstance(item, dict):
            raise VocabularyResponseError("EPSG item must be a JSON object")
        code = item.get("Code")
        label = item.get("Name")
        if isinstance(code, bool) or not isinstance(code, (int, str)):
            raise VocabularyResponseError("EPSG item has an invalid code")
        identifier = str(code)
        if not _IDENTIFIER_PATTERN.fullmatch(identifier):
            raise VocabularyResponseError("EPSG item has an invalid code")
        if not isinstance(label, str) or not label.strip():
            raise VocabularyResponseError("EPSG item has an invalid name")
        description = item.get("Remark" if lookup else "Remarks")
        if description is not None and not isinstance(description, str):
            raise VocabularyResponseError("EPSG item has invalid remarks")
        return VocabularyEntry(
            id=identifier,
            label=label.strip(),
            description=description.strip() if description else None,
            vocabulary=VOCABULARY,
        )
