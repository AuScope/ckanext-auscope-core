"""Read-only Research Organization Registry (ROR) v2 client."""

from dataclasses import dataclass
from functools import partial
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

DEFAULT_BASE_URL = "https://api.ror.org/v2/organizations"
ROR_URI = "https://ror.org/"
_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
_QUERY_PUNCTUATION = re.compile(r'[+\-=&|><!(){}\[\]^"~*?:\\/]')
_SHORT_ID = r"0[0-9a-hj-km-np-tv-z]{6}[0-9]{2}"
_IDENTIFIER = re.compile(rf"(?:(?:https://)?ror\.org/)?({_SHORT_ID})")


def normalize_ror_id(value: object) -> str:
    """Validate the syntax and checksum and return the canonical HTTPS URL."""
    if not isinstance(value, str) or not value.isascii():
        raise InvalidVocabularyInput("Enter a ROR identifier or HTTPS ROR URL.")
    match = _IDENTIFIER.fullmatch(value.strip().lower())
    if not match:
        raise InvalidVocabularyInput("Enter a ROR identifier or HTTPS ROR URL.")
    identifier = match[1]
    number = 0
    for character in identifier[:-2]:
        number = number * 32 + _ALPHABET.index(character)
    if int(identifier[-2:]) != 98 - (number * 100 % 97):
        raise InvalidVocabularyInput("The ROR identifier checksum is invalid.")
    return ROR_URI + identifier


@dataclass(frozen=True, slots=True)
class RorOrganisation(VocabularyEntry):
    status: str = "active"

    def as_dict(self) -> dict[str, str]:
        return {**VocabularyEntry.as_dict(self), "status": self.status}


class RorClient:
    """Find active organisations or resolve an ID with any registry status."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        connect_timeout: int = 3,
        read_timeout: int = 10,
        default_limit: int = 20,
        max_limit: int = 50,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
        http_get=None,
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
        self.http_get = http_get or partial(requests.get, allow_redirects=False)

    def _get(self, url, params=None):
        try:
            return get_json(
                self.http_get, url, params=params, timeout=self.timeout,
                max_response_bytes=self.max_response_bytes,
            )
        except VocabularyProviderError as error:
            if error.status_code == 429:
                raise VocabularyProviderError("ROR rate limit reached") from error
            raise

    def search(
        self, query: str, *, limit: int | str | None = None
    ) -> list[RorOrganisation]:
        """Search by name, or resolve a pasted ID if it is active."""
        query = validate_query(query)
        limit = validate_limit(limit, self.default_limit, self.max_limit)
        if query.lower().startswith(("https://ror.org/", "ror.org/")) or (
            _IDENTIFIER.fullmatch(query.lower())
        ):
            try:
                organisation = self.lookup(query)
            except VocabularyNotFound:
                return []
            return [organisation] if organisation.status == "active" else []

        escaped_query = _QUERY_PUNCTUATION.sub(lambda match: "\\" + match[0], query)
        data = self._get(self.base_url, {"query": escaped_query})
        items = data.get("items")
        if not isinstance(items, list):
            raise VocabularyResponseError("ROR search response is missing items")
        entries = [self._normalize(item) for item in items]
        return [entry for entry in entries if entry.status == "active"][:limit]

    def lookup(self, identifier: str) -> RorOrganisation:
        canonical = normalize_ror_id(identifier)
        try:
            data = self._get(f"{self.base_url}/{canonical.removeprefix(ROR_URI)}")
        except VocabularyProviderError as error:
            if error.status_code == 404:
                raise VocabularyNotFound("ROR identifier was not found.") from error
            raise
        organisation = self._normalize(data)
        if organisation.id != canonical:
            raise VocabularyResponseError("ROR lookup returned a different identifier")
        return organisation

    @staticmethod
    def _normalize(item: object) -> RorOrganisation:
        if not isinstance(item, dict):
            raise VocabularyResponseError("ROR record must be an object")
        try:
            identifier = normalize_ror_id(item.get("id"))
        except InvalidVocabularyInput as error:
            raise VocabularyResponseError("ROR record has an invalid ID") from error
        status = item.get("status")
        if status not in ("active", "inactive", "withdrawn"):
            raise VocabularyResponseError("ROR record has an invalid status")

        names = item.get("names")
        if not isinstance(names, list):
            raise VocabularyResponseError("ROR record is missing names")
        candidates = []
        for name in names:
            if not isinstance(name, dict):
                continue
            value, types = name.get("value"), name.get("types")
            if isinstance(value, str) and value.strip():
                if isinstance(types, list) and "ror_display" in types:
                    candidates.insert(0, value.strip())
                    break
                candidates.append(value.strip())
        if not candidates:
            raise VocabularyResponseError("ROR record has no display name")

        countries = {}
        locations = item.get("locations")
        if not isinstance(locations, list):
            locations = []
        for location in locations:
            if isinstance(location, dict):
                details = location.get("geonames_details")
                if isinstance(details, dict):
                    country = details.get("country_name")
                    if isinstance(country, str) and country.strip():
                        countries[country.strip()] = None
        return RorOrganisation(
            id=identifier,
            label=candidates[0],
            vocabulary="Research Organization Registry",
            description=", ".join(countries) or None,
            status=status,
        )
