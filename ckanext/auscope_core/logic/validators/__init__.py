"""Dependency-free validators exposed by AuScope Core."""

from ckanext.auscope_core.logic.validators.geographic import (
    GeographicValidationError,
    is_valid_bounding_box,
    is_valid_geojson,
    is_valid_latitude,
    is_valid_longitude,
    parse_bounding_box,
    parse_latitude,
    parse_longitude,
    validate_geojson,
    validate_position,
)

__all__ = [
    "GeographicValidationError",
    "is_valid_bounding_box",
    "is_valid_geojson",
    "is_valid_latitude",
    "is_valid_longitude",
    "parse_bounding_box",
    "parse_latitude",
    "parse_longitude",
    "validate_geojson",
    "validate_position",
]
