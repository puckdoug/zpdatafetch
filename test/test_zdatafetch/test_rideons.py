"""Tests for Zwift RideOn data fetching."""

import json

from zdatafetch.rideons import ZwiftRideOns


def test_rideons_initialization():
  """Test ZwiftRideOns initialization."""
  rideons = ZwiftRideOns()

  assert rideons._raw == ""
  assert rideons._fetched == {}
  assert rideons.rider_id == 0
  assert rideons.activity_id == 0
  assert rideons.rideons == []


def test_parse_response():
  """Test parsing raw RideOn data."""
  rideons = ZwiftRideOns()
  rideons.rider_id = 550564
  rideons.activity_id = 12345678

  rideons._raw = json.dumps(
    [
      {"id": 123456, "firstName": "John", "lastName": "Doe"},
      {"id": 789012, "firstName": "Jane", "lastName": "Smith"},
    ],
  )

  rideons._parse_response()

  assert len(rideons.rideons) == 2
  assert rideons.rideons[0]["id"] == 123456
  assert rideons.rideons[1]["id"] == 789012


def test_rideon_count():
  """Test RideOn count helper."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    {"id": 1},
    {"id": 2},
    {"id": 3},
  ]

  assert rideons.rideon_count() == 3


def test_rideon_ids():
  """Test extracting rider IDs who gave RideOns."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    {"id": 123, "firstName": "John"},
    {"id": 456, "firstName": "Jane"},
  ]

  ids = rideons.rideon_ids()
  assert ids == [123, 456]


def test_has_rideon_from():
  """Test checking if specific rider gave RideOn."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    {"id": 123, "firstName": "John"},
    {"id": 456, "firstName": "Jane"},
  ]

  assert rideons.has_rideon_from(123) is True
  assert rideons.has_rideon_from(456) is True
  assert rideons.has_rideon_from(999) is False


def test_str_representation():
  """Test string representation."""
  rideons = ZwiftRideOns()
  rideons.rider_id = 550564
  rideons.activity_id = 12345678
  rideons.rideons = [{"id": 1}, {"id": 2}]
  rideons._fetched = {"rideons": rideons.rideons}

  output = str(rideons)
  assert "ZwiftRideOns(rider_id=550564, activity_id=12345678)" in output
  assert "rideons:" in output


def test_json_serialization():
  """Test JSON serialization."""
  rideons = ZwiftRideOns()
  rideons._fetched = {
    "rideons": [
      {"id": 123, "firstName": "John"},
      {"id": 456, "firstName": "Jane"},
    ],
  }

  json_str = rideons.json()
  data = json.loads(json_str)
  assert "rideons" in data
  assert len(data["rideons"]) == 2


def test_asdict():
  """Test dictionary access."""
  rideons = ZwiftRideOns()
  rideons._fetched = {"rideons": []}

  data = rideons.asdict()
  assert isinstance(data, dict)
  assert "rideons" in data


def test_parse_empty_response():
  """Test parsing empty RideOn list."""
  rideons = ZwiftRideOns()
  rideons._raw = "[]"
  rideons._parse_response()

  assert rideons.rideons == []
  assert rideons.rideon_count() == 0


def test_parse_malformed_response():
  """Test parsing malformed response."""
  rideons = ZwiftRideOns()
  rideons._raw = '{"invalid": "not an array"}'
  rideons._parse_response()

  assert rideons.rideons == []
  assert rideons._fetched == {"rideons": []}
