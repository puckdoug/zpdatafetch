"""Tests for RaceFinish class."""

import json
from pathlib import Path

import pytest

from zpdatafetch.race_finish import RaceFinish


@pytest.fixture
def sample_race_data():
  """Sample race data from actual API response."""
  return {
    "DT_RowId": "",
    "ftp": "139",
    "friend": 0,
    "pt": "",
    "label": "5",
    "zid": "5230175",
    "pos": 112,
    "position_in_cat": 2,
    "name": "TessGames Tessachka (DIRT)",
    "cp": 1,
    "zwid": 7574336,
    "event_title": "Stage 1: Fresh Outta 25: Prospect Park Loop",
    "event_date": 1764799800,
    "avg_power": [123, 0],
    "avg_wkg": ["2.5", 0],
    "distance": 22,
    "laps": "4",
    "category": "E",
  }


@pytest.fixture
def race_finish(sample_race_data):
  """Create a RaceFinish instance."""
  return RaceFinish(sample_race_data)


class TestRaceFinishInitialization:
  """Test RaceFinish initialization."""

  def test_init_stores_data(self, sample_race_data):
    """Test that initialization stores the race data."""
    race = RaceFinish(sample_race_data)
    assert race._data == sample_race_data

  def test_init_with_empty_dict(self):
    """Test initialization with empty dictionary."""
    race = RaceFinish({})
    assert race._data == {}


class TestRaceFinishAttributeAccess:
  """Test attribute-style access to race data."""

  def test_getattr_returns_field_value(self, race_finish):
    """Test accessing fields via attributes."""
    assert race_finish.event_title == "Stage 1: Fresh Outta 25: Prospect Park Loop"
    assert race_finish.pos == 112
    assert race_finish.zwid == 7574336

  def test_getattr_returns_complex_values(self, race_finish):
    """Test accessing fields with complex values (lists, etc)."""
    assert race_finish.avg_power == [123, 0]
    assert race_finish.avg_wkg == ["2.5", 0]

  def test_getattr_missing_field_raises_attribute_error(self, race_finish):
    """Test accessing non-existent field raises AttributeError."""
    with pytest.raises(AttributeError) as exc_info:
      _ = race_finish.nonexistent_field
    assert "nonexistent_field" in str(exc_info.value)

  def test_getattr_private_field_raises_attribute_error(self, race_finish):
    """Test accessing private fields raises AttributeError."""
    with pytest.raises(AttributeError):
      _ = race_finish._nonexistent


class TestRaceFinishDictAccess:
  """Test dictionary-style access to race data."""

  def test_getitem_returns_field_value(self, race_finish):
    """Test accessing fields via dictionary syntax."""
    assert race_finish["event_title"] == "Stage 1: Fresh Outta 25: Prospect Park Loop"
    assert race_finish["pos"] == 112
    assert race_finish["zwid"] == 7574336

  def test_getitem_missing_field_raises_key_error(self, race_finish):
    """Test accessing non-existent field raises KeyError."""
    with pytest.raises(KeyError):
      _ = race_finish["nonexistent_field"]

  def test_getitem_and_getattr_return_same_value(self, race_finish):
    """Test that dict and attribute access return the same value."""
    assert race_finish["event_title"] == race_finish.event_title
    assert race_finish["pos"] == race_finish.pos
    assert race_finish["avg_power"] == race_finish.avg_power


class TestRaceFinishRepr:
  """Test string representation."""

  def test_repr_contains_event_and_position(self, race_finish):
    """Test repr shows event title and position."""
    repr_str = repr(race_finish)
    assert "RaceFinish" in repr_str
    assert "Prospect Park Loop" in repr_str
    assert "112" in repr_str

  def test_repr_handles_missing_fields(self):
    """Test repr handles missing event_title or pos."""
    race = RaceFinish({"zid": "123"})
    repr_str = repr(race)
    assert "RaceFinish" in repr_str
    assert "Unknown" in repr_str

  def test_repr_handles_empty_data(self):
    """Test repr with completely empty data."""
    race = RaceFinish({})
    repr_str = repr(race)
    assert "RaceFinish" in repr_str


class TestRaceFinishAsdict:
  """Test serialization back to dictionary."""

  def test_asdict_returns_original_data(self, race_finish, sample_race_data):
    """Test asdict returns the original dictionary."""
    result = race_finish.asdict()
    assert result == sample_race_data

  def test_asdict_returns_copy_reference(self, race_finish):
    """Test that asdict returns reference to internal data."""
    result = race_finish.asdict()
    # Should be same reference (not a copy)
    assert result is race_finish._data

  def test_asdict_with_empty_data(self):
    """Test asdict with empty race data."""
    race = RaceFinish({})
    assert race.asdict() == {}


class TestRaceFinishWithRealData:
  """Test RaceFinish with real fixture data."""

  @pytest.fixture
  def real_race_data(self):
    """Load real race data from fixture file."""
    fixture_path = Path(__file__).parent.parent.parent / "tmp" / "7574336_all.json"
    if not fixture_path.exists():
      pytest.skip("Fixture file not available")

    with open(fixture_path) as f:
      data = json.load(f)

    if not data.get("data") or len(data["data"]) == 0:
      pytest.skip("No race data in fixture")

    return data["data"][0]

  def test_real_race_data_has_expected_fields(self, real_race_data):
    """Test that real race data has expected fields."""
    race = RaceFinish(real_race_data)

    # Check core fields exist
    assert hasattr(race, "zid")
    assert hasattr(race, "event_title")
    assert hasattr(race, "pos")
    assert hasattr(race, "zwid")

  def test_real_race_data_attribute_access(self, real_race_data):
    """Test attribute access with real data."""
    race = RaceFinish(real_race_data)

    # Should not raise
    _ = race.event_title
    _ = race.pos
    _ = race.avg_power

  def test_real_race_data_serialization(self, real_race_data):
    """Test that real data can be serialized back."""
    race = RaceFinish(real_race_data)
    result = race.asdict()

    # Should be able to serialize to JSON
    json_str = json.dumps(result)
    assert len(json_str) > 0
