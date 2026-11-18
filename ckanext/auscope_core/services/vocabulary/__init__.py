"""Shared FOR and EPSG vocabulary clients."""

from ckanext.auscope_core.services.vocabulary.base import (
    InvalidVocabularyInput,
    VocabularyConfigurationError,
    VocabularyEntry,
    VocabularyError,
    VocabularyNotFound,
    VocabularyProviderError,
    VocabularyResponseError,
)
from ckanext.auscope_core.services.vocabulary.epsg import EpsgVocabularyClient
from ckanext.auscope_core.services.vocabulary.for_ardc import ForVocabularyClient

__all__ = [
    "EpsgVocabularyClient",
    "ForVocabularyClient",
    "InvalidVocabularyInput",
    "VocabularyConfigurationError",
    "VocabularyEntry",
    "VocabularyError",
    "VocabularyNotFound",
    "VocabularyProviderError",
    "VocabularyResponseError",
]
