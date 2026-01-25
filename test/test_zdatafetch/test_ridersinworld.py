"""Tests for Zwift riders in world data fetching."""

import json

from zdatafetch.ridersinworld import ZwiftRidersInWorld


def test_ridersinworld_initialization():
  """Test ZwiftRidersInWorld initialization."""
  riders = ZwiftRidersInWorld()

  assert riders._raw == ''
  assert riders._fetched == {}
  assert riders.world_id == 0
  assert riders.riders == []


def test_parse_response_with_friends():
  """Test parsing raw riders data with friendsInWorld."""
  riders = ZwiftRidersInWorld()
  riders.world_id = 1

  raw_json = json.dumps(
    {
      'worldId': 1,
      'friendsInWorld': [
        {'id': 550564, 'firstName': 'Doug', 'lastName': 'Morris'},
        {'id': 123456, 'firstName': 'Jane', 'lastName': 'Doe'},
      ],
    }
  )

  riders._parse_response(raw_json)

  assert len(riders.riders) == 2
  assert riders.riders[0]['id'] == 550564


def test_parse_response_with_player_list():
  """Test parsing raw riders data with playerEntryList."""
  riders = ZwiftRidersInWorld()
  riders.world_id = 1

  raw_json = json.dumps(
    {
      'worldId': 1,
      'playerEntryList': [
        {'id': 550564, 'firstName': 'Doug'},
        {'id': 123456, 'firstName': 'Jane'},
      ],
    }
  )

  riders._parse_response(raw_json)

  assert len(riders.riders) == 2
  assert riders.riders[0]['id'] == 550564


def test_rider_count():
  """Test rider count helper."""
  riders = ZwiftRidersInWorld()
  riders.riders = [
    {'id': 1},
    {'id': 2},
    {'id': 3},
  ]

  assert riders.rider_count() == 3


def test_rider_ids():
  """Test extracting rider IDs."""
  riders = ZwiftRidersInWorld()
  riders.riders = [
    {'id': 123, 'firstName': 'John'},
    {'id': 456, 'firstName': 'Jane'},
  ]

  ids = riders.rider_ids()
  assert ids == [123, 456]


def test_str_representation():
  """Test string representation."""
  riders = ZwiftRidersInWorld()
  riders.world_id = 1
  riders.riders = [{'id': 1}, {'id': 2}]
  riders._fetched = {'worldId': 1, 'friendsInWorld': riders.riders}

  output = str(riders)
  assert 'ZwiftRidersInWorld(world_id=1)' in output
  assert 'worldId:' in output


def test_json_serialization():
  """Test JSON serialization."""
  riders = ZwiftRidersInWorld()
  riders._fetched = {
    'worldId': 1,
    'friendsInWorld': [
      {'id': 123, 'firstName': 'John'},
      {'id': 456, 'firstName': 'Jane'},
    ],
  }

  json_str = riders.json()
  data = json.loads(json_str)
  assert 'worldId' in data
  assert 'friendsInWorld' in data


def test_asdict():
  """Test dictionary access."""
  riders = ZwiftRidersInWorld()
  riders._fetched = {'worldId': 1}

  data = riders.asdict()
  assert isinstance(data, dict)
  assert 'worldId' in data


def test_parse_empty_world():
  """Test parsing world with no riders."""
  riders = ZwiftRidersInWorld()
  riders._parse_response('{"worldId": 1}')

  assert riders.riders == []
  assert riders.rider_count() == 0


def test_parse_malformed_response():
  """Test parsing malformed response."""
  riders = ZwiftRidersInWorld()
  riders._parse_response('"not a dict"')

  assert riders.riders == []
  assert riders._fetched == {'riders': []}
