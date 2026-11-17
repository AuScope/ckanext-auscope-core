"""Tests for dependency-free shared geographic validation primitives."""

import json
from pathlib import Path

import pytest

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

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "geographic_legacy_contracts.json"


@pytest.fixture(scope="module")
def legacy_contracts():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_coordinate_contract_fixture(legacy_contracts):
    validators = {
        "latitude": is_valid_latitude,
        "longitude": is_valid_longitude,
    }
    for case in legacy_contracts["coordinate_cases"]:
        assert validators[case["kind"]](case["value"]) is case["shared_valid"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-90, -90.0), ("-12.5", -12.5), (0, 0.0), (90, 90.0)],
)
def test_parse_latitude_accepts_boundaries_and_numeric_strings(value, expected):
    assert parse_latitude(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(-180, -180.0), ("115.86", 115.86), (0, 0.0), (180, 180.0)],
)
def test_parse_longitude_accepts_boundaries_and_numeric_strings(value, expected):
    assert parse_longitude(value) == expected


@pytest.mark.parametrize(
    "parser,value",
    [
        (parse_latitude, -90.01),
        (parse_latitude, 90.01),
        (parse_longitude, -180.01),
        (parse_longitude, 180.01),
        (parse_latitude, None),
        (parse_latitude, ""),
        (parse_longitude, " "),
        (parse_longitude, "not-a-number"),
        (parse_latitude, True),
        (parse_longitude, False),
        (parse_latitude, float("nan")),
        (parse_longitude, float("inf")),
        (parse_longitude, float("-inf")),
    ],
)
def test_coordinate_parsers_reject_invalid_and_non_finite_values(parser, value):
    with pytest.raises(GeographicValidationError):
        parser(value)


def test_validate_position_uses_longitude_latitude_order():
    assert validate_position([115.86, -31.95]) == (115.86, -31.95)
    assert validate_position([115.86, -31.95, "25"]) == (115.86, -31.95, 25.0)


@pytest.mark.parametrize(
    "value",
    [
        [-31.95, 181],
        [115.86],
        [115.86, -31.95, float("nan")],
        "115.86,-31.95",
        None,
    ],
)
def test_validate_position_rejects_wrong_order_shape_or_non_finite_values(value):
    with pytest.raises(GeographicValidationError):
        validate_position(value)


def test_bounding_box_contract_fixture(legacy_contracts):
    for case in legacy_contracts["bounding_box_cases"]:
        assert is_valid_bounding_box(case["value"]) is case["shared_valid"]


def test_geojson_contract_fixture(legacy_contracts):
    for case in legacy_contracts["geojson_cases"]:
        assert is_valid_geojson(
            case["value"],
            expected_geometry_type=case["expected_geometry_type"],
        ) is case["shared_valid"]


@pytest.mark.parametrize(
    "value",
    [
        "110,-45,155,-10",
        ["110,-45,155,-10"],
        [110, -45, 155, -10],
        (110, -45, 155, -10),
    ],
)
def test_parse_bounding_box_accepts_supported_input_shapes(value):
    assert parse_bounding_box(value) == (110.0, -45.0, 155.0, -10.0)


@pytest.mark.parametrize(
    "value",
    [
        "",
        None,
        "110,-45,155",
        "110,-45,155,-10,1",
        ["110", "-45"],
        "west,-45,155,-10",
        "110,-45,inf,-10",
        "110,-45,155,nan",
        "155,-45,110,-10",
        "110,-10,155,-45",
        "110,-45,110,-10",
        "110,-45,155,-45",
        "170,-10,-170,10",
    ],
)
def test_parse_bounding_box_rejects_malformed_reversed_and_crossing_values(value):
    with pytest.raises(GeographicValidationError):
        parse_bounding_box(value)


POINT = {"type": "Point", "coordinates": [115.86, -31.95]}
POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [115.0, -32.0],
            [116.0, -32.0],
            [116.0, -31.0],
            [115.0, -32.0],
        ]
    ],
}


@pytest.mark.parametrize(
    "value",
    [
        POINT,
        {"type": "Feature", "properties": {}, "geometry": POINT},
        {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {}, "geometry": POINT}
            ],
        },
        json.dumps(POINT),
    ],
)
def test_validate_geojson_accepts_point_geometry_feature_and_collection(value):
    assert validate_geojson(value, expected_geometry_type="Point")["type"]


def test_validate_geojson_accepts_polygon_and_multiple_features():
    collection = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {}, "geometry": POLYGON},
            {"type": "Feature", "properties": {}, "geometry": POLYGON},
        ],
    }
    assert is_valid_geojson(collection, expected_geometry_type="Polygon")


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not-json",
        [],
        {},
        {"type": "FeatureCollection"},
        {"type": "FeatureCollection", "features": []},
        {"type": "Feature", "properties": {}},
        {"type": "Feature", "geometry": None},
        {"type": "FeatureCollection", "features": [POINT]},
        {"type": "LineString", "coordinates": [[115, -32], [116, -31]]},
        {"type": "Point"},
        {"type": "Point", "coordinates": []},
        {"type": "Point", "coordinates": [181, 0]},
        {"type": "Point", "coordinates": [115, float("nan")]},
        {"type": "Polygon", "coordinates": []},
        {"type": "Polygon", "coordinates": [[[115, -32], [116, -31]]]},
        {
            "type": "Polygon",
            "coordinates": [
                [[115, -32], [116, -32], [116, -31], [115, -31]]
            ],
        },
    ],
)
def test_validate_geojson_rejects_empty_malformed_and_non_finite_values(value):
    with pytest.raises(GeographicValidationError):
        validate_geojson(value)


@pytest.mark.parametrize(
    ("geometry", "expected"),
    [(POINT, "Polygon"), (POLYGON, "Point")],
)
def test_validate_geojson_rejects_geometry_type_mismatches(geometry, expected):
    assert not is_valid_geojson(geometry, expected_geometry_type=expected)
    with pytest.raises(GeographicValidationError, match="expected"):
        validate_geojson(geometry, expected_geometry_type=expected)


def test_validate_geojson_rejects_unknown_expected_type():
    with pytest.raises(GeographicValidationError, match="expected geometry type"):
        validate_geojson(POINT, expected_geometry_type="LineString")
