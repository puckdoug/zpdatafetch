"""Tests for Racelog class."""

import json
from pathlib import Path

import pytest

from zpdatafetch.race_finish import RaceFinish
from zpdatafetch.racelog import Racelog


@pytest.fixture
def sample_race_list():
  """Sample list of race data."""
  return [
    {
      "zid": "5230175",
      "pos": 112,
      "event_title": "Stage 1: Fresh Outta 25: Prospect Park Loop",
      "event_date": 1764799800,
      "avg_power": [123, 0],
      "zwid": 7574336,
    },
    {
      "zid": "5236642",
      "pos": 29,
      "event_title": "Zwift Epic Race - Snowman",
      "event_date": 1765065600,
      "avg_power": [107, 0],
      "zwid": 7574336,
    },
    {
      "zid": "5254836",
      "pos": 200,
      "event_title": "Zwift Racing League: City Showdown",
      "event_date": 1765306980,
      "avg_power": [137, 1],
      "zwid": 7574336,
    },
  ]


@pytest.fixture
def racelog(sample_race_list):
  """Create a Racelog instance."""
  return Racelog(sample_race_list)


class TestRacelogInitialization:
  """Test Racelog initialization."""

  def test_init_creates_race_finish_objects(self, sample_race_list):
    """Test that initialization creates RaceFinish objects."""
    racelog = Racelog(sample_race_list)
    assert len(racelog._races) == 3
    assert all(isinstance(race, RaceFinish) for race in racelog._races)

  def test_init_with_empty_list(self):
    """Test initialization with empty list."""
    racelog = Racelog([])
    assert len(racelog._races) == 0

  def test_init_preserves_race_data(self, sample_race_list):
    """Test that race data is preserved correctly."""
    racelog = Racelog(sample_race_list)
    assert (
      racelog._races[0].event_title == 'Stage 1: Fresh Outta 25: Prospect Park Loop'
    )
    assert racelog._races[1].pos == 29


class TestRacelogLen:
  """Test len() functionality."""

  def test_len_returns_race_count(self, racelog):
    """Test that len() returns number of races."""
    assert len(racelog) == 3

  def test_len_empty_racelog(self):
    """Test len() with empty racelog."""
    racelog = Racelog([])
    assert len(racelog) == 0

  def test_len_single_race(self):
    """Test len() with single race."""
    racelog = Racelog([{"zid": "123", "pos": 1}])
    assert len(racelog) == 1


class TestRacelogIndexing:
  """Test indexing functionality."""

  def test_getitem_positive_index(self, racelog):
    """Test accessing races by positive index."""
    first_race = racelog[0]
    assert isinstance(first_race, RaceFinish)
    assert first_race.pos == 112

  def test_getitem_negative_index(self, racelog):
    """Test accessing races by negative index."""
    last_race = racelog[-1]
    assert isinstance(last_race, RaceFinish)
    assert last_race.pos == 200

  def test_getitem_middle_index(self, racelog):
    """Test accessing middle element."""
    second_race = racelog[1]
    assert second_race.pos == 29

  def test_getitem_out_of_range_raises_index_error(self, racelog):
    """Test that out of range index raises IndexError."""
    with pytest.raises(IndexError):
      _ = racelog[10]

  def test_getitem_negative_out_of_range(self, racelog):
    """Test that negative out of range raises IndexError."""
    with pytest.raises(IndexError):
      _ = racelog[-10]


class TestRacelogSlicing:
  """Test slicing functionality."""

  def test_slice_returns_list_of_races(self, racelog):
    """Test that slicing returns a list of RaceFinish objects."""
    races = racelog[0:2]
    assert isinstance(races, list)
    assert len(races) == 2
    assert all(isinstance(race, RaceFinish) for race in races)

  def test_slice_first_two(self, racelog):
    """Test slicing first two races."""
    races = racelog[0:2]
    assert races[0].pos == 112
    assert races[1].pos == 29

  def test_slice_last_two(self, racelog):
    """Test slicing last two races."""
    races = racelog[-2:]
    assert len(races) == 2
    assert races[0].pos == 29
    assert races[1].pos == 200

  def test_slice_with_step(self, racelog):
    """Test slicing with step."""
    races = racelog[::2]  # Every other race
    assert len(races) == 2
    assert races[0].pos == 112
    assert races[1].pos == 200

  def test_slice_empty_result(self, racelog):
    """Test slicing that returns empty list."""
    races = racelog[10:20]
    assert races == []

  def test_slice_all(self, racelog):
    """Test slicing entire racelog."""
    races = racelog[:]
    assert len(races) == 3


class TestRacelogIteration:
  """Test iteration functionality."""

  def test_iter_yields_race_finish_objects(self, racelog):
    """Test that iteration yields RaceFinish objects."""
    races = list(racelog)
    assert len(races) == 3
    assert all(isinstance(race, RaceFinish) for race in races)

  def test_iter_in_for_loop(self, racelog):
    """Test iteration in for loop."""
    positions = []
    for race in racelog:
      positions.append(race.pos)
    assert positions == [112, 29, 200]

  def test_iter_empty_racelog(self):
    """Test iteration over empty racelog."""
    racelog = Racelog([])
    races = list(racelog)
    assert races == []

  def test_iter_with_enumerate(self, racelog):
    """Test iteration with enumerate."""
    for idx, race in enumerate(racelog):
      assert isinstance(race, RaceFinish)
      if idx == 0:
        assert race.pos == 112


class TestRacelogRepr:
  """Test string representation."""

  def test_repr_shows_race_count(self, racelog):
    """Test repr shows number of races."""
    repr_str = repr(racelog)
    assert "Racelog" in repr_str
    assert "3 races" in repr_str

  def test_repr_empty_racelog(self):
    """Test repr with empty racelog."""
    racelog = Racelog([])
    repr_str = repr(racelog)
    assert "Racelog" in repr_str
    assert "0 races" in repr_str

  def test_repr_single_race(self):
    """Test repr with single race."""
    racelog = Racelog([{"zid": "123", "pos": 1}])
    repr_str = repr(racelog)
    assert "1 races" in repr_str


class TestRacelogAslist:
  """Test serialization to list."""

  def test_aslist_returns_list_of_dicts(self, racelog, sample_race_list):
    """Test aslist returns list of dictionaries."""
    result = racelog.aslist()
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(item, dict) for item in result)

  def test_aslist_preserves_data(self, racelog, sample_race_list):
    """Test that aslist preserves original data."""
    result = racelog.aslist()
    assert result[0]["pos"] == 112
    assert result[1]["event_title"] == "Zwift Epic Race - Snowman"
    assert result[2]["avg_power"] == [137, 1]

  def test_aslist_roundtrip(self, racelog):
    """Test that data can roundtrip through aslist."""
    original_list = racelog.aslist()
    new_racelog = Racelog(original_list)
    assert len(new_racelog) == len(racelog)
    assert new_racelog.aslist() == original_list

  def test_aslist_empty_racelog(self):
    """Test aslist with empty racelog."""
    racelog = Racelog([])
    assert racelog.aslist() == []

  def test_aslist_serializable_to_json(self, racelog):
    """Test that aslist result can be serialized to JSON."""
    result = racelog.aslist()
    json_str = json.dumps(result)
    assert len(json_str) > 0

    # Verify it can be parsed back
    parsed = json.loads(json_str)
    assert len(parsed) == 3


class TestRacelogWithRealData:
  """Test Racelog with real fixture data."""

  @pytest.fixture
  def real_racelog(self):
    """Load real racelog from fixture file."""
    fixture_path = Path(__file__).parent.parent.parent / "tmp" / "7574336_all.json"
    if not fixture_path.exists():
      pytest.skip("Fixture file not available")

    with open(fixture_path) as f:
      data = json.load(f)

    if not data.get("data"):
      pytest.skip("No race data in fixture")

    return Racelog(data["data"])

  def test_real_data_len(self, real_racelog):
    """Test len() with real data."""
    assert len(real_racelog) > 0

  def test_real_data_indexing(self, real_racelog):
    """Test indexing with real data."""
    first_race = real_racelog[0]
    assert isinstance(first_race, RaceFinish)
    assert hasattr(first_race, "event_title")

  def test_real_data_iteration(self, real_racelog):
    """Test iteration with real data."""
    count = 0
    for race in real_racelog:
      assert isinstance(race, RaceFinish)
      count += 1
    assert count == len(real_racelog)

  def test_real_data_slicing(self, real_racelog):
    """Test slicing with real data."""
    if len(real_racelog) >= 3:
      races = real_racelog[0:3]
      assert len(races) == 3

  def test_real_data_aslist(self, real_racelog):
    """Test aslist with real data."""
    result = real_racelog.aslist()
    assert isinstance(result, list)
    assert len(result) == len(real_racelog)

    # Verify JSON serialization
    json_str = json.dumps(result)
    assert len(json_str) > 0

  def test_real_data_large_dataset(self):
    """Test with larger dataset (550564_all.json)."""
    fixture_path = Path(__file__).parent.parent.parent / "tmp" / "550564_all.json"
    if not fixture_path.exists():
      pytest.skip("Large fixture file not available")

    with open(fixture_path) as f:
      data = json.load(f)

    if not data.get("data"):
      pytest.skip("No race data in large fixture")

    racelog = Racelog(data["data"])

    # Should handle large dataset
    assert len(racelog) > 0

    # Test iteration doesn't crash
    count = 0
    for race in racelog:
      count += 1
      if count > 10:  # Just test first 10 to save time
        break

    # Test slicing
    if len(racelog) >= 10:
      subset = racelog[0:10]
      assert len(subset) == 10
