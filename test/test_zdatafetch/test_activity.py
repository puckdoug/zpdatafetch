"""Tests for Zwift activity data fetching."""

import json

from zdatafetch.activity import ZwiftActivity


def test_activity_initialization():
  """Test ZwiftActivity initialization."""
  activity = ZwiftActivity()

  assert activity._raw == ""
  assert activity._fetched == {}
  assert activity.rider_id == 0
  assert activity.start == 0
  assert activity.limit == 20
  assert activity.activities == []


def test_parse_response():
  """Test parsing raw activity data."""
  activity = ZwiftActivity()
  activity.rider_id = 550564

  raw_json = json.dumps(
    [
      {'id': 12345, 'name': 'Morning Ride', 'distanceInMeters': 50000},
      {'id': 12346, 'name': 'Evening Ride', 'distanceInMeters': 30000},
    ]
  )

  activity._parse_response(raw_json)

  assert len(activity.activities) == 2
  assert activity.activities[0]["id"] == 12345
  assert activity.activities[1]["id"] == 12346


def test_activity_count():
  """Test activity count helper."""
  activity = ZwiftActivity()
  activity.activities = [
    {"id": 1},
    {"id": 2},
    {"id": 3},
  ]

  assert activity.activity_count() == 3


def test_activity_ids():
  """Test extracting activity IDs."""
  activity = ZwiftActivity()
  activity.activities = [
    {"id": 123, "name": "Ride 1"},
    {"id": 456, "name": "Ride 2"},
  ]

  ids = activity.activity_ids()
  assert ids == [123, 456]


def test_str_representation():
  """Test string representation."""
  activity = ZwiftActivity()
  activity.rider_id = 550564
  activity.start = 0
  activity.limit = 20
  activity.activities = [{"id": 1}, {"id": 2}]
  activity._fetched = {"activities": activity.activities}

  output = str(activity)
  assert "ZwiftActivity(rider_id=550564, start=0, limit=20)" in output
  assert "activities:" in output


def test_json_serialization():
  """Test JSON serialization."""
  activity = ZwiftActivity()
  activity._fetched = {
    "activities": [
      {"id": 123, "name": "Ride 1"},
      {"id": 456, "name": "Ride 2"},
    ],
  }

  json_str = activity.json()
  data = json.loads(json_str)
  assert "activities" in data
  assert len(data["activities"]) == 2


def test_asdict():
  """Test dictionary access."""
  activity = ZwiftActivity()
  activity._fetched = {"activities": []}

  data = activity.asdict()
  assert isinstance(data, dict)
  assert "activities" in data


def test_parse_empty_response():
  """Test parsing empty activity list."""
  activity = ZwiftActivity()
  activity._parse_response("[]")

  assert activity.activities == []
  assert activity.activity_count() == 0


def test_parse_malformed_response():
  """Test parsing malformed response."""
  activity = ZwiftActivity()
  activity._parse_response('{"invalid": "not an array"}')

  assert activity.activities == []
  assert activity._fetched == {"activities": []}
