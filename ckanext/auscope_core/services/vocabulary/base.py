"""Small shared contracts for external vocabulary clients."""

from dataclasses import dataclass
import json
import math
from typing import Any
from urllib.parse import urlsplit

import requests

MAX_QUERY_LENGTH = 100
MAX_RESPONSE_BYTES = 1_000_000


class VocabularyError(Exception):
    """Base class for expected vocabulary service errors."""


class InvalidVocabularyInput(VocabularyError, ValueError):
    """A query, identifier or result limit is invalid."""


class VocabularyConfigurationError(VocabularyError, ValueError):
    """Vocabulary client or CKAN configuration is invalid."""


class VocabularyNotFound(VocabularyError, LookupError):
    """The requested vocabulary identifier does not exist."""


class VocabularyProviderError(VocabularyError):
    """The external vocabulary provider could not be reached or failed."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class VocabularyResponseError(VocabularyError):
    """The external provider returned an unsafe or malformed response."""


@dataclass(frozen=True, slots=True)
class VocabularyEntry:
    """Provider-neutral vocabulary entry."""

    id: str
    label: str
    vocabulary: str
    description: str | None = None

    def as_dict(self) -> dict[str, str]:
        """Return the stable JSON/Python representation."""
        result = {
            "id": self.id,
            "label": self.label,
            "vocabulary": self.vocabulary,
        }
        if self.description:
            result["description"] = self.description
        return result


def validate_query(query: object) -> str:
    """Validate and normalize a search query."""
    if not isinstance(query, str):
        raise InvalidVocabularyInput("query must be a string")
    query = query.strip()
    if not query:
        raise InvalidVocabularyInput("query must not be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise InvalidVocabularyInput(
            f"query must be at most {MAX_QUERY_LENGTH} characters"
        )
    return query


def validate_limit(limit: object, default: int, maximum: int) -> int:
    """Validate a requested result limit against configured bounds."""
    if limit is None:
        return default
    if isinstance(limit, bool):
        raise InvalidVocabularyInput("limit must be an integer")
    try:
        parsed = int(limit)
    except (TypeError, ValueError) as error:
        raise InvalidVocabularyInput("limit must be an integer") from error
    if parsed < 1 or parsed > maximum:
        raise InvalidVocabularyInput(f"limit must be between 1 and {maximum}")
    return parsed


def validate_client_configuration(
    *,
    connect_timeout: object,
    read_timeout: object,
    default_limit: object,
    max_limit: object,
    max_response_bytes: object,
    urls: dict[str, object],
) -> None:
    """Fail fast when client or CKAN provider configuration is invalid."""
    for name, value in (
        ("connect_timeout", connect_timeout),
        ("read_timeout", read_timeout),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise VocabularyConfigurationError(f"{name} must be greater than 0")

    for name, value in (
        ("default_limit", default_limit),
        ("max_limit", max_limit),
        ("max_response_bytes", max_response_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise VocabularyConfigurationError(
                f"{name} must be a positive integer"
            )
    if default_limit > max_limit:
        raise VocabularyConfigurationError(
            "default_limit must be less than or equal to max_limit"
        )

    for name, value in urls.items():
        if not isinstance(value, str) or not value or value != value.strip():
            raise VocabularyConfigurationError(
                f"{name} must be a non-empty HTTP or HTTPS URL"
            )
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as error:
            raise VocabularyConfigurationError(
                f"{name} must be a valid HTTP or HTTPS URL"
            ) from error
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.query
            or parsed.fragment
            or port is not None
            and not 1 <= port <= 65535
        ):
            raise VocabularyConfigurationError(
                f"{name} must be a valid HTTP or HTTPS base URL"
            )


def get_json(
    http_get,
    url: str,
    *,
    params: dict[str, Any] | None,
    timeout: tuple[int, int],
    max_response_bytes: int = MAX_RESPONSE_BYTES,
) -> dict[str, Any]:
    """GET and validate a bounded JSON object without leaking provider details."""
    try:
        response = http_get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=timeout,
            stream=True,
        )
        try:
            if not 200 <= response.status_code < 300:
                raise VocabularyProviderError(
                    "vocabulary provider request failed",
                    status_code=response.status_code,
                )

            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    declared_length = int(content_length)
                except ValueError as error:
                    raise VocabularyResponseError(
                        "vocabulary response has an invalid content length"
                    ) from error
                if declared_length < 0:
                    raise VocabularyResponseError(
                        "vocabulary response has an invalid content length"
                    )
                if declared_length > max_response_bytes:
                    raise VocabularyResponseError("vocabulary response is too large")

            chunks = []
            response_size = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                if not isinstance(chunk, bytes):
                    raise VocabularyResponseError(
                        "vocabulary response contains invalid content"
                    )
                response_size += len(chunk)
                if response_size > max_response_bytes:
                    raise VocabularyResponseError("vocabulary response is too large")
                chunks.append(chunk)

            try:
                data = json.loads(b"".join(chunks))
            except (TypeError, ValueError) as error:
                raise VocabularyResponseError(
                    "vocabulary response is not valid JSON"
                ) from error
            if not isinstance(data, dict):
                raise VocabularyResponseError(
                    "vocabulary response must be a JSON object"
                )
            return data
        finally:
            response.close()
    except requests.RequestException as error:
        raise VocabularyProviderError("vocabulary provider unavailable") from error
