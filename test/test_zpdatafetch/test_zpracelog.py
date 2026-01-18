"""Tests for Racelog class."""

import json
import time
from pathlib import Path

import pytest

from zpdatafetch.zpracefinish import ZPRaceFinish
from zpdatafetch.zpracelog import ZPRacelog


def test_zpracelog_empty_instantiation():
  """Test that ZPRacelog can be instantiated with no arguments."""
  obj = ZPRacelog()
  assert obj is not None
  assert len(obj) == 0
  assert obj.aslist() == []


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
  return ZPRacelog(sample_race_list)


class TestRacelogInitialization:
  """Test Racelog initialization."""

  def test_init_creates_race_finish_objects(self, sample_race_list):
    """Test that initialization creates RaceFinish objects."""
    racelog = ZPRacelog(sample_race_list)
    assert len(racelog._races) == 3
    assert all(isinstance(race, ZPRaceFinish) for race in racelog._races)

  def test_init_with_empty_list(self):
    """Test initialization with empty list."""
    racelog = ZPRacelog([])
    assert len(racelog._races) == 0

  def test_init_preserves_race_data(self, sample_race_list):
    """Test that race data is preserved correctly."""
    racelog = ZPRacelog(sample_race_list)
    assert (
      racelog._races[0].event_title == "Stage 1: Fresh Outta 25: Prospect Park Loop"
    )
    assert racelog._races[1].pos == 29


class TestRacelogLen:
  """Test len() functionality."""

  def test_len_returns_race_count(self, racelog):
    """Test that len() returns number of races."""
    assert len(racelog) == 3

  def test_len_empty_racelog(self):
    """Test len() with empty racelog."""
    racelog = ZPRacelog([])
    assert len(racelog) == 0

  def test_len_single_race(self):
    """Test len() with single race."""
    racelog = ZPRacelog([{"zid": "123", "pos": 1}])
    assert len(racelog) == 1


class TestRacelogIndexing:
  """Test indexing functionality."""

  def test_getitem_positive_index(self, racelog):
    """Test accessing races by positive index."""
    first_race = racelog[0]
    assert isinstance(first_race, ZPRaceFinish)
    assert first_race.pos == 112

  def test_getitem_negative_index(self, racelog):
    """Test accessing races by negative index."""
    last_race = racelog[-1]
    assert isinstance(last_race, ZPRaceFinish)
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
    assert all(isinstance(race, ZPRaceFinish) for race in races)

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
    assert all(isinstance(race, ZPRaceFinish) for race in races)

  def test_iter_in_for_loop(self, racelog):
    """Test iteration in for loop."""
    positions = []
    for race in racelog:
      positions.append(race.pos)
    assert positions == [112, 29, 200]

  def test_iter_empty_racelog(self):
    """Test iteration over empty racelog."""
    racelog = ZPRacelog([])
    races = list(racelog)
    assert races == []

  def test_iter_with_enumerate(self, racelog):
    """Test iteration with enumerate."""
    for idx, race in enumerate(racelog):
      assert isinstance(race, ZPRaceFinish)
      if idx == 0:
        assert race.pos == 112


class TestRacelogRepr:
  """Test string representation."""

  def test_repr_shows_all_races(self, racelog):
    """Test repr shows all races."""
    repr_str = repr(racelog)
    assert "Racelog([" in repr_str
    assert "ZPRaceFinish(" in repr_str
    # Should have 3 RaceFinish entries
    assert repr_str.count("ZPRaceFinish(") == 3
    # Should be multi-line
    assert "\n" in repr_str
    assert "])" in repr_str

  def test_repr_empty_racelog(self):
    """Test repr with empty racelog."""
    racelog = ZPRacelog([])
    repr_str = repr(racelog)
    assert repr_str == "ZPRacelog([])"

  def test_repr_single_race(self):
    """Test repr with single race."""
    racelog = ZPRacelog([{"zid": "123", "pos": 1}])
    repr_str = repr(racelog)
    assert "Racelog([" in repr_str
    assert "ZPRaceFinish(" in repr_str
    assert "zid='123'" in repr_str
    assert "pos=1" in repr_str

  def test_str_shows_all_races(self, racelog):
    """Test str shows all races in requested format."""
    str_repr = str(racelog)
    assert "ZPRacelog[" in str_repr
    assert "ZPRaceFinish(" in str_repr
    # Should have 3 RaceFinish entries
    assert str_repr.count("ZPRaceFinish(") == 3
    # Should be multi-line
    assert "\n" in str_repr
    assert "]" in str_repr

  def test_str_empty_racelog(self):
    """Test str with empty racelog."""
    racelog = ZPRacelog([])
    str_repr = str(racelog)
    assert str_repr == "ZPRacelog[]"

  def test_str_single_race(self):
    """Test str with single race."""
    racelog = ZPRacelog([{"zid": "123", "pos": 1}])
    str_repr = str(racelog)
    assert "ZPRacelog[" in str_repr
    assert "ZPRaceFinish(" in str_repr
    assert "zid='123'" in str_repr


class TestRacelogAslist:
  """Test serialization to list."""

  def test_aslist_returns_list_of_dicts(self, racelog, sample_race_list):
    """Test aslist returns list of dictionaries."""
    result = racelog.aslist()
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(item, dict) for item in result)

  def test_aslist_preserves_data(self, racelog, sample_race_list):
    """Test that aslist preserves cleaned data."""
    result = racelog.aslist()
    assert result[0]["pos"] == 112
    assert result[1]["event_title"] == "Zwift Epic Race - Snowman"
    # avg_power should be cleaned to scalar
    assert result[2]["avg_power"] == 137

  def test_aslist_roundtrip(self, racelog):
    """Test that data can roundtrip through aslist."""
    original_list = racelog.aslist()
    new_racelog = ZPRacelog(original_list)
    assert len(new_racelog) == len(racelog)
    assert new_racelog.aslist() == original_list

  def test_aslist_empty_racelog(self):
    """Test aslist with empty racelog."""
    racelog = ZPRacelog([])
    assert racelog.aslist() == []

  def test_aslist_serializable_to_json(self, racelog):
    """Test that aslist result can be serialized to JSON."""
    result = racelog.aslist()
    json_str = json.dumps(result)
    assert len(json_str) > 0

    # Verify it can be parsed back
    parsed = json.loads(json_str)
    assert len(parsed) == 3


class TestRacelogDaysLast:
  """Test Racelog.days_last() filtering method."""

  def test_days_last_returns_racelog(self):
    """Test that days_last() returns a Racelog object."""
    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": int(time.time())},
      ],
    )
    recent = racelog.days_last(30)
    assert isinstance(recent, ZPRacelog)

  def test_days_last_includes_recent_races(self):
    """Test that days_last(30) includes races from last 30 days."""
    now = time.time()
    ten_days_ago = now - (10 * 24 * 60 * 60)

    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": int(ten_days_ago), "pos": 1},
        {"zid": "2", "event_date": int(now), "pos": 2},
      ],
    )

    recent = racelog.days_last(30)
    assert len(recent) == 2

  def test_days_last_excludes_old_races(self):
    """Test that days_last(30) excludes races older than 30 days."""
    now = time.time()
    forty_days_ago = now - (40 * 24 * 60 * 60)

    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": int(forty_days_ago), "pos": 1},
      ],
    )

    recent = racelog.days_last(30)
    assert len(recent) == 0

  def test_days_last_mixed_old_and_recent(self):
    """Test filtering with mix of old and recent races."""
    now = time.time()
    five_days_ago = now - (5 * 24 * 60 * 60)
    twenty_days_ago = now - (20 * 24 * 60 * 60)
    forty_days_ago = now - (40 * 24 * 60 * 60)
    sixty_days_ago = now - (60 * 24 * 60 * 60)

    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": int(sixty_days_ago), "event_title": "Old 1"},
        {"zid": "2", "event_date": int(twenty_days_ago), "event_title": "Recent 1"},
        {"zid": "3", "event_date": int(forty_days_ago), "event_title": "Old 2"},
        {"zid": "4", "event_date": int(five_days_ago), "event_title": "Recent 2"},
        {"zid": "5", "event_date": int(now), "event_title": "Recent 3"},
      ],
    )

    recent = racelog.days_last(30)
    assert len(recent) == 3

    # Verify correct races included
    titles = [race.event_title for race in recent]
    assert "Recent 1" in titles
    assert "Recent 2" in titles
    assert "Recent 3" in titles
    assert "Old 1" not in titles
    assert "Old 2" not in titles

  def test_days_last_handles_missing_event_date(self):
    """Test that races without event_date are excluded."""
    now = time.time()

    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": int(now), "pos": 1},
        {"zid": "2", "pos": 2},  # Missing event_date
      ],
    )

    recent = racelog.days_last(30)
    assert len(recent) == 1

  def test_days_last_empty_racelog(self):
    """Test days_last() with empty racelog."""
    racelog = ZPRacelog([])
    recent = racelog.days_last(30)
    assert len(recent) == 0
    assert isinstance(recent, ZPRacelog)

  def test_days_last_preserves_race_data(self):
    """Test that days_last() preserves all race data fields."""
    now = time.time()

    racelog = ZPRacelog(
      [
        {
          "zid": "123",
          "event_date": int(now),
          "event_title": "Test Race",
          "pos": 42,
          "avg_power": [200, 0],
        },
      ],
    )

    recent = racelog.days_last(30)
    assert len(recent) == 1
    race = recent[0]
    assert race.zid == "123"
    assert race.event_title == "Test Race"
    assert race.pos == 42
    # avg_power should be cleaned to scalar
    assert race.avg_power == 200

  def test_days_last_returns_new_racelog(self):
    """Test that days_last() returns a new Racelog, not modifying original."""
    now = time.time()

    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": int(now)},
      ],
    )

    original_len = len(racelog)
    recent = racelog.days_last(30)

    # Original should be unchanged
    assert len(racelog) == original_len
    # New racelog should be separate object
    assert recent is not racelog

  def test_days_last_boundary_case(self):
    """Test races near 30 day boundary."""
    now = time.time()
    # Use integer arithmetic to avoid precision issues
    thirty_days_seconds = 30 * 24 * 60 * 60
    cutoff = int(now - thirty_days_seconds)

    # Just under 30 days (should be included)
    just_recent = cutoff + 1
    # Just over 30 days (should be excluded)
    just_old = cutoff - 1

    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": just_recent, "event_title": "Recent"},
        {"zid": "2", "event_date": just_old, "event_title": "Old"},
      ],
    )

    recent = racelog.days_last(30)
    # Should only include the recent race
    assert len(recent) == 1
    assert recent[0].event_title == "Recent"

  def test_days_last_different_periods(self):
    """Test days_last() with different time periods."""
    now = time.time()
    # Use values safely within boundaries (not at exact edges)
    five_days_ago = now - (5 * 24 * 60 * 60)
    forty_days_ago = now - (40 * 24 * 60 * 60)
    eighty_days_ago = now - (80 * 24 * 60 * 60)

    racelog = ZPRacelog(
      [
        {"zid": "1", "event_date": int(five_days_ago), "event_title": "Week"},
        {"zid": "2", "event_date": int(forty_days_ago), "event_title": "45d"},
        {"zid": "3", "event_date": int(eighty_days_ago), "event_title": "90d"},
      ],
    )

    # Test 7 days - should get race from 5 days ago
    last_7 = racelog.days_last(7)
    assert len(last_7) == 1
    assert last_7[0].event_title == "Week"

    # Test 30 days - should still get only the 5 day old race
    last_30 = racelog.days_last(30)
    assert len(last_30) == 1
    assert last_30[0].event_title == "Week"

    # Test 60 days - should get both 5 and 40 day old races
    last_60 = racelog.days_last(60)
    assert len(last_60) == 2
    titles = [race.event_title for race in last_60]
    assert "Week" in titles
    assert "45d" in titles

    # Test 100 days - should get all races
    last_100 = racelog.days_last(100)
    assert len(last_100) == 3


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

    return ZPRacelog(data["data"])

  def test_real_data_len(self, real_racelog):
    """Test len() with real data."""
    assert len(real_racelog) > 0

  def test_real_data_indexing(self, real_racelog):
    """Test indexing with real data."""
    first_race = real_racelog[0]
    assert isinstance(first_race, ZPRaceFinish)
    assert hasattr(first_race, "event_title")

  def test_real_data_iteration(self, real_racelog):
    """Test iteration with real data."""
    count = 0
    for race in real_racelog:
      assert isinstance(race, ZPRaceFinish)
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

    racelog = ZPRacelog(data["data"])

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
