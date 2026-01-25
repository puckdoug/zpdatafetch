"""Tests for Cyclist.racelog() method."""

import json
from pathlib import Path

import httpx
import pytest

from zpdatafetch.zpcyclist import ZPCyclist
from zpdatafetch.zpcyclistfetch import ZPCyclistFetch
from zpdatafetch.zpracefinish import ZPRaceFinish
from zpdatafetch.zpracelog import ZPRacelog


@pytest.fixture
def mock_cyclist_data():
  """Mock cyclist data with race log."""
  return {
    'data': [
      {
        'zid': '5230175',
        'pos': 112,
        'event_title': 'Race 1',
        'zwid': 7574336,
      },
      {
        'zid': '5236642',
        'pos': 29,
        'event_title': 'Race 2',
        'zwid': 7574336,
      },
    ],
  }


@pytest.fixture
def mock_transport(mock_cyclist_data):
  """Create a mock transport for httpx."""

  def handler(request) -> httpx.Response:
    return httpx.Response(
      200,
      json=mock_cyclist_data,
    )

  return httpx.MockTransport(handler)


class TestCyclistRacelogMethod:
  """Test Cyclist.racelog() method."""

  def test_racelog_returns_racelog_object(self, mock_cyclist_data):
    """Test that racelog() returns a Racelog object."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[7574336] = ZPCyclist(mock_cyclist_data)

    racelog = cyclist.racelog(7574336)
    assert isinstance(racelog, ZPRacelog)

  def test_racelog_contains_correct_number_of_races(self, mock_cyclist_data):
    """Test that racelog contains correct number of races."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[7574336] = ZPCyclist(mock_cyclist_data)

    racelog = cyclist.racelog(7574336)
    assert len(racelog) == 2

  def test_racelog_races_are_race_finish_objects(self, mock_cyclist_data):
    """Test that races in racelog are RaceFinish objects."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[7574336] = ZPCyclist(mock_cyclist_data)

    racelog = cyclist.racelog(7574336)
    for race in racelog:
      assert isinstance(race, ZPRaceFinish)

  def test_racelog_preserves_race_data(self, mock_cyclist_data):
    """Test that racelog preserves race data correctly."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[7574336] = ZPCyclist(mock_cyclist_data)

    racelog = cyclist.racelog(7574336)
    assert racelog[0].event_title == 'Race 1'
    assert racelog[0].position == 112
    assert racelog[1].event_title == 'Race 2'
    assert racelog[1].position == 29


class TestCyclistRacelogErrors:
  """Test error handling in Cyclist.racelog()."""

  def test_racelog_raises_value_error_if_not_fetched(self):
    """Test that racelog() raises ValueError if data not fetched."""
    cyclist = ZPCyclistFetch()

    with pytest.raises(ValueError) as exc_info:
      cyclist.racelog(123456)

    assert 'No data fetched' in str(exc_info.value)
    assert '123456' in str(exc_info.value)

  def test_racelog_raises_key_error_if_missing_data_key(self):
    """Test that racelog() raises KeyError if 'data' key missing."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[999] = ZPCyclist({})  # Missing 'data' key

    with pytest.raises(KeyError) as exc_info:
      cyclist.racelog(999)

    assert 'missing' in str(exc_info.value).lower()
    assert 'data' in str(exc_info.value).lower()

  def test_racelog_error_message_suggests_fetch(self):
    """Test that error message suggests calling fetch()."""
    cyclist = ZPCyclistFetch()

    with pytest.raises(ValueError) as exc_info:
      cyclist.racelog(123456)

    assert 'fetch()' in str(exc_info.value) or 'afetch()' in str(exc_info.value)


class TestCyclistRacelogWithEmptyData:
  """Test Cyclist.racelog() with edge cases."""

  def test_racelog_with_empty_data_array(self):
    """Test racelog with empty data array."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[123] = ZPCyclist({'data': []})

    racelog = cyclist.racelog(123)
    assert isinstance(racelog, ZPRacelog)
    assert len(racelog) == 0

  def test_racelog_with_single_race(self):
    """Test racelog with single race."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[123] = ZPCyclist(
      {
        'data': [
          {'zid': '123', 'pos': 1, 'event_title': 'Test Race'},
        ],
      },
    )

    racelog = cyclist.racelog(123)
    assert len(racelog) == 1
    assert racelog[0].event_title == 'Test Race'


class TestCyclistRacelogIntegration:
  """Integration tests for Cyclist.racelog() with mocked HTTP."""

  def test_fetch_and_racelog_workflow(self, mock_cyclist_data):
    """Test complete workflow: set data then racelog."""
    cyclist = ZPCyclistFetch()

    # Simulate fetched data
    cyclist._fetched[7574336] = ZPCyclist(mock_cyclist_data)

    # Verify data was fetched
    assert 7574336 in cyclist._fetched

    # Get racelog
    racelog = cyclist.racelog(7574336)

    # Verify racelog
    assert isinstance(racelog, ZPRacelog)
    assert len(racelog) > 0

  def test_multiple_cyclists_separate_racelogs(self):
    """Test that different cyclists have separate racelogs."""
    cyclist = ZPCyclistFetch()

    # Mock data for two different cyclists
    cyclist._fetched[111] = ZPCyclist(
      {
        'data': [
          {'zid': '1', 'pos': 1},
          {'zid': '2', 'pos': 2},
        ],
      },
    )
    cyclist._fetched[222] = ZPCyclist(
      {
        'data': [
          {'zid': '3', 'pos': 3},
        ],
      },
    )

    racelog1 = cyclist.racelog(111)
    racelog2 = cyclist.racelog(222)

    assert len(racelog1) == 2
    assert len(racelog2) == 1


class TestCyclistRacelogWithRealFixture:
  """Test Cyclist.racelog() with real fixture data."""

  @pytest.fixture
  def real_cyclist_data(self):
    """Load real cyclist data from fixture."""
    fixture_path = (
      Path(__file__).parent.parent.parent / 'tmp' / '7574336_all.json'
    )
    if not fixture_path.exists():
      pytest.skip('Fixture file not available')

    with open(fixture_path) as f:
      return json.load(f)

  def test_racelog_with_real_data(self, real_cyclist_data):
    """Test racelog with real fixture data."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[7574336] = ZPCyclist(real_cyclist_data)

    racelog = cyclist.racelog(7574336)

    assert isinstance(racelog, ZPRacelog)
    assert len(racelog) > 0

    # Test that we can iterate
    for race in racelog:
      assert isinstance(race, ZPRaceFinish)
      assert hasattr(race, 'event_title')

  def test_racelog_serialization_with_real_data(self, real_cyclist_data):
    """Test that racelog from real data can be serialized."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[7574336] = ZPCyclist(real_cyclist_data)

    racelog = cyclist.racelog(7574336)
    result = racelog.aslist()

    # Should be able to serialize to JSON
    json_str = json.dumps(result)
    assert len(json_str) > 0

  def test_racelog_access_patterns_with_real_data(self, real_cyclist_data):
    """Test various access patterns with real data."""
    cyclist = ZPCyclistFetch()
    cyclist._fetched[7574336] = ZPCyclist(real_cyclist_data)

    racelog = cyclist.racelog(7574336)

    if len(racelog) > 0:
      # Test indexing
      first_race = racelog[0]
      assert isinstance(first_race, ZPRaceFinish)

      # Test slicing
      if len(racelog) >= 3:
        subset = racelog[0:3]
        assert len(subset) == 3

      # Test attribute access
      _ = first_race.event_title
      _ = first_race.position

  def test_large_racelog(self):
    """Test with large racelog (550564_all.json)."""
    fixture_path = (
      Path(__file__).parent.parent.parent / 'tmp' / '550564_all.json'
    )
    if not fixture_path.exists():
      pytest.skip('Large fixture file not available')

    with open(fixture_path) as f:
      data = json.load(f)

    cyclist = ZPCyclistFetch()
    cyclist._fetched[550564] = ZPCyclist(data)

    racelog = cyclist.racelog(550564)

    # Should handle large dataset
    assert isinstance(racelog, ZPRacelog)
    assert len(racelog) > 0

    # Test that iteration works
    count = 0
    for race in racelog:
      count += 1
      if count > 10:  # Just verify first 10
        break

    assert count > 0
