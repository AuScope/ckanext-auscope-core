"""Pure geographic validation primitives shared by AuScope repositories.

Coordinates use GeoJSON order: longitude first, latitude second. The helpers only
validate and parse values. They do not decide whether a location is required,
transform coordinate reference systems or update a spatial index.

Bounding boxes use ``west,south,east,north`` order. They deliberately require
``west < east`` and therefore reject antimeridian-crossing boxes. Consumers that
need antimeridian support must represent and index it under an explicit local
policy rather than relying on silent longitude wrapping.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import math
from typing import Any

SUPPORTED_GEOMETRY_TYPES = frozenset({"Point", "Polygon"})


class GeographicValidationError(ValueError):
    """Raised when a geographic value does not satisfy the shared contract."""


def _parse_finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or value is None:
        raise GeographicValidationError(f"{label} must be a finite number")

    if isinstance(value, str) and not value.strip():
        raise GeographicValidationError(f"{label} must be a finite number")

    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise GeographicValidationError(
            f"{label} must be a finite number"
        ) from error

    if not math.isfinite(number):
        raise GeographicValidationError(f"{label} must be a finite number")
    return number


def parse_latitude(value: Any) -> float:
    """Return *value* as a finite latitude in the inclusive range -90 to 90."""

    latitude = _parse_finite_number(value, "latitude")
    if not -90 <= latitude <= 90:
        raise GeographicValidationError("latitude must be between -90 and 90")
    return latitude


def parse_longitude(value: Any) -> float:
    """Return *value* as a finite longitude in the inclusive range -180 to 180."""

    longitude = _parse_finite_number(value, "longitude")
    if not -180 <= longitude <= 180:
        raise GeographicValidationError("longitude must be between -180 and 180")
    return longitude


def is_valid_latitude(value: Any) -> bool:
    """Return whether *value* is a valid latitude."""

    try:
        parse_latitude(value)
    except GeographicValidationError:
        return False
    return True


def is_valid_longitude(value: Any) -> bool:
    """Return whether *value* is a valid longitude."""

    try:
        parse_longitude(value)
    except GeographicValidationError:
        return False
    return True


def _is_coordinate_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def validate_position(value: Any) -> tuple[float, ...]:
    """Validate a GeoJSON position and return its numeric coordinate tuple.

    The first two values are interpreted as longitude and latitude. Optional
    additional dimensions are permitted but must also be finite numbers.
    """

    if not _is_coordinate_sequence(value) or len(value) < 2:
        raise GeographicValidationError(
            "position must contain longitude and latitude"
        )

    coordinates = [parse_longitude(value[0]), parse_latitude(value[1])]
    coordinates.extend(
        _parse_finite_number(extra, "additional coordinate") for extra in value[2:]
    )
    return tuple(coordinates)


def parse_bounding_box(value: Any) -> tuple[float, float, float, float]:
    """Parse and validate a ``west,south,east,north`` bounding box.

    Comma-separated strings, four-item sequences and the legacy one-item list
    containing a comma-separated string are accepted. Equal or reversed bounds
    are rejected. Because west must be less than east, a box cannot cross the
    antimeridian.
    """

    if (
        _is_coordinate_sequence(value)
        and len(value) == 1
        and isinstance(value[0], str)
    ):
        value = value[0]

    parts: Any
    if isinstance(value, str):
        if not value.strip():
            raise GeographicValidationError("bounding box must not be empty")
        parts = value.split(",")
    elif _is_coordinate_sequence(value):
        parts = value
    else:
        raise GeographicValidationError(
            "bounding box must contain west, south, east and north"
        )

    if len(parts) != 4:
        raise GeographicValidationError(
            "bounding box must contain west, south, east and north"
        )

    west = parse_longitude(parts[0])
    south = parse_latitude(parts[1])
    east = parse_longitude(parts[2])
    north = parse_latitude(parts[3])

    if west >= east:
        raise GeographicValidationError(
            "bounding box west must be less than east; "
            "antimeridian crossing is not supported"
        )
    if south >= north:
        raise GeographicValidationError(
            "bounding box south must be less than north"
        )
    return west, south, east, north


def is_valid_bounding_box(value: Any) -> bool:
    """Return whether *value* is a valid non-antimeridian bounding box."""

    try:
        parse_bounding_box(value)
    except GeographicValidationError:
        return False
    return True


def _validate_geometry(
    geometry: Any, expected_geometry_type: str | None
) -> None:
    if not isinstance(geometry, Mapping):
        raise GeographicValidationError("geometry must be an object")

    geometry_type = geometry.get("type")
    if geometry_type not in SUPPORTED_GEOMETRY_TYPES:
        raise GeographicValidationError(
            "geometry type must be Point or Polygon"
        )
    if expected_geometry_type and geometry_type != expected_geometry_type:
        raise GeographicValidationError(
            f"expected {expected_geometry_type} geometry, got {geometry_type}"
        )
    if "coordinates" not in geometry:
        raise GeographicValidationError("geometry coordinates are required")

    coordinates = geometry["coordinates"]
    if geometry_type == "Point":
        validate_position(coordinates)
        return

    if not _is_coordinate_sequence(coordinates) or not coordinates:
        raise GeographicValidationError(
            "Polygon coordinates must contain at least one linear ring"
        )

    for ring in coordinates:
        if not _is_coordinate_sequence(ring) or len(ring) < 4:
            raise GeographicValidationError(
                "each Polygon linear ring must contain at least four positions"
            )
        positions = [validate_position(position) for position in ring]
        if positions[0] != positions[-1]:
            raise GeographicValidationError(
                "each Polygon linear ring must be closed"
            )


def _validate_feature(feature: Any, expected_geometry_type: str | None) -> None:
    if not isinstance(feature, Mapping) or feature.get("type") != "Feature":
        raise GeographicValidationError("feature must be a GeoJSON Feature")
    if "geometry" not in feature or feature["geometry"] is None:
        raise GeographicValidationError("feature geometry is required")
    _validate_geometry(feature["geometry"], expected_geometry_type)


def validate_geojson(
    value: Any, *, expected_geometry_type: str | None = None
) -> dict[str, Any]:
    """Validate Point or Polygon GeoJSON and return its parsed object.

    *value* may be a JSON string or a mapping containing a geometry, Feature or
    non-empty FeatureCollection. When ``expected_geometry_type`` is supplied,
    every geometry must have that type. Only Point and Polygon are supported.

    The returned object is not transformed and no CRS or spatial-index operation
    is performed.
    """

    if expected_geometry_type not in SUPPORTED_GEOMETRY_TYPES | {None}:
        raise GeographicValidationError(
            "expected geometry type must be Point or Polygon"
        )

    if isinstance(value, str):
        if not value.strip():
            raise GeographicValidationError("GeoJSON must not be empty")
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError) as error:
            raise GeographicValidationError("GeoJSON is not valid JSON") from error

    if not isinstance(value, Mapping):
        raise GeographicValidationError("GeoJSON must be an object")

    object_type = value.get("type")
    if object_type == "FeatureCollection":
        features = value.get("features")
        if not _is_coordinate_sequence(features) or not features:
            raise GeographicValidationError(
                "FeatureCollection must contain at least one feature"
            )
        for feature in features:
            _validate_feature(feature, expected_geometry_type)
    elif object_type == "Feature":
        _validate_feature(value, expected_geometry_type)
    elif object_type in SUPPORTED_GEOMETRY_TYPES:
        _validate_geometry(value, expected_geometry_type)
    else:
        raise GeographicValidationError(
            "GeoJSON type must be FeatureCollection, Feature, Point or Polygon"
        )

    return dict(value)


def is_valid_geojson(
    value: Any, *, expected_geometry_type: str | None = None
) -> bool:
    """Return whether *value* satisfies the shared Point/Polygon contract."""

    try:
        validate_geojson(value, expected_geometry_type=expected_geometry_type)
    except GeographicValidationError:
        return False
    return True
