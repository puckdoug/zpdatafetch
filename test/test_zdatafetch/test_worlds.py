"""Tests for Zwift worlds data fetching."""

import json

from zdatafetch.worlds import ZwiftWorlds, get_world_id, get_world_name


def test_worlds_initialization():
  """Test ZwiftWorlds initialization."""
  worlds = ZwiftWorlds()

  assert worlds._raw == ''
  assert worlds._fetched == {}
  assert worlds.worlds == []


def test_parse_response():
  """Test parsing raw worlds data."""
  worlds = ZwiftWorlds()

  raw_json = json.dumps(
    [
      {'worldId': 1, 'name': 'Watopia', 'playerCount': 1000},
      {'worldId': 3, 'name': 'London', 'playerCount': 500},
    ]
  )

  worlds._parse_response(raw_json)

  assert len(worlds.worlds) == 2
  assert worlds.worlds[0]['worldId'] == 1
  assert worlds.worlds[1]['worldId'] == 3


def test_world_count():
  """Test world count helper."""
  worlds = ZwiftWorlds()
  worlds.worlds = [
    {'worldId': 1},
    {'worldId': 3},
  ]

  assert worlds.world_count() == 2


def test_world_ids():
  """Test extracting world IDs."""
  worlds = ZwiftWorlds()
  worlds.worlds = [
    {'worldId': 1, 'name': 'Watopia'},
    {'worldId': 3, 'name': 'London'},
  ]

  ids = worlds.world_ids()
  assert ids == [1, 3]


def test_world_names():
  """Test extracting world names."""
  worlds = ZwiftWorlds()
  worlds.worlds = [
    {'worldId': 1},
    {'worldId': 3},
    {'worldId': 99},  # Unknown world
  ]

  names = worlds.world_names()
  assert 'Watopia' in names
  assert 'London' in names
  assert 'Unknown(99)' in names


def test_get_world_id():
  """Test world ID lookup by name."""
  assert get_world_id('watopia') == 1
  assert get_world_id('Watopia') == 1
  assert get_world_id('WATOPIA') == 1
  assert get_world_id('london') == 3
  assert get_world_id('makuri') == 9
  assert get_world_id('makuriislands') == 9
  assert get_world_id('unknown') is None


def test_get_world_name():
  """Test world name lookup by ID."""
  assert get_world_name(1) == 'Watopia'
  assert get_world_name(3) == 'London'
  assert get_world_name(9) == 'Makuri'
  assert get_world_name(99) is None


def test_str_representation():
  """Test string representation."""
  worlds = ZwiftWorlds()
  worlds.worlds = [{'worldId': 1}, {'worldId': 3}]
  worlds._fetched = {'worlds': worlds.worlds}

  output = str(worlds)
  assert 'ZwiftWorlds()' in output
  assert 'worlds:' in output


def test_json_serialization():
  """Test JSON serialization."""
  worlds = ZwiftWorlds()
  worlds._fetched = {
    'worlds': [
      {'worldId': 1, 'name': 'Watopia'},
      {'worldId': 3, 'name': 'London'},
    ],
  }

  json_str = worlds.json()
  data = json.loads(json_str)
  assert 'worlds' in data
  assert len(data['worlds']) == 2


def test_asdict():
  """Test dictionary access."""
  worlds = ZwiftWorlds()
  worlds._fetched = {'worlds': []}

  data = worlds.asdict()
  assert isinstance(data, dict)
  assert 'worlds' in data


def test_parse_empty_response():
  """Test parsing empty worlds list."""
  worlds = ZwiftWorlds()
  worlds._parse_response('[]')

  assert worlds.worlds == []
  assert worlds.world_count() == 0


def test_parse_malformed_response():
  """Test parsing malformed response (string instead of dict/list)."""
  worlds = ZwiftWorlds()
  worlds._parse_response('"just a string"')

  assert worlds.worlds == []
  assert worlds._fetched == {'worlds': []}
