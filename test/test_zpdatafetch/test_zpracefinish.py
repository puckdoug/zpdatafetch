"""Tests for RaceFinish class."""

import json
from pathlib import Path

import pytest

from zpdatafetch.zpracefinish import ZPRaceFinish


def test_zpracefinish_empty_instantiation():
  """Test that ZPRaceFinish can be instantiated with no arguments."""
  obj = ZPRaceFinish()
  assert obj is not None
  # Empty race finish includes default converted fields
  assert obj.asdict() == {
    'category': '',
    'category_women': '',
    'time': 0.0,
    'time_hms': '',
    'time_gun': 0.0,
    'time_gun_hms': '',
    'event_date': '',
  }


@pytest.fixture
def sample_race_data():
  """Sample race data from actual API response."""
  return {
    'DT_RowId': '',
    'ftp': '139',
    'friend': 0,
    'pt': '',
    'label': '5',
    'zid': '5230175',
    'pos': 112,
    'position_in_cat': 2,
    'name': 'TessGames Tessachka (DIRT)',
    'cp': 1,
    'zwid': 7574336,
    'event_title': 'Stage 1: Fresh Outta 25: Prospect Park Loop',
    'event_date': 1764799800,
    'avg_power': [123, 0],
    'avg_wkg': ['2.5', 0],
    'distance': 22,
    'laps': '4',
    'category': 'E',
  }


@pytest.fixture
def race_finish(sample_race_data):
  """Create a RaceFinish instance."""
  return ZPRaceFinish(sample_race_data)


class TestRaceFinishInitialization:
  """Test RaceFinish initialization."""

  def test_init_stores_data(self, sample_race_data):
    """Test that initialization stores the race data."""
    race = ZPRaceFinish(sample_race_data)
    # Data should be cleaned, not identical to input
    assert race._data is not sample_race_data
    # Excluded fields should NOT be in _data, only in _excluded
    excluded_field_names = {
      'DT_RowId',
      'friend',
      'pt',
      'label',
      'tc',
      'tbc',
      'tbd',
      'reg',
      'fl',
      'info',
      'info_note',
      'strike',
      'f_t',
      'rt',
      'dur',
      'pts_pos',
      'pts',
      'is_guess',
      'note',
      'src',
      'power_type',
      'zeff',
      'info_notes',
    }
    for excluded_key in excluded_field_names:
      if excluded_key in sample_race_data:
        assert excluded_key not in race._data, (
          f'{excluded_key} should be in _excluded, not _data'
        )
        assert excluded_key in race._excluded, f'{excluded_key} should be in _excluded'
    # Field names should be mapped - only new names in _data, not old ones
    field_mapping = {'ftp': 'zftp', 'zid': 'zwift_id', 'pos': 'position'}
    for orig_key, mapped_key in field_mapping.items():
      if orig_key in sample_race_data and orig_key not in excluded_field_names:
        # New name should be present
        assert mapped_key in race._data, f'{mapped_key} should be in _data'
        # Old name should NOT be present
        assert orig_key not in race._data, (
          f'{orig_key} should NOT be in _data (renamed to {mapped_key})'
        )

  def test_init_with_empty_dict(self):
    """Test initialization with empty dictionary."""
    race = ZPRaceFinish({})
    # Empty race finish includes default converted fields
    assert race._data == {
      'category': '',
      'category_women': '',
      'time': 0.0,
      'time_hms': '',
      'time_gun': 0.0,
      'time_gun_hms': '',
      'event_date': '',
    }

  def test_init_cleans_array_fields(self):
    """Test that array fields are cleaned to scalar values."""
    data = {
      'zid': '123',
      'avg_power': [150, 0],
      'avg_wkg': ['3.0', 1],
      'weight': ['50.0', 1],
      'time': [3600.5, 0],
      'np': [160, 0],
    }
    race = ZPRaceFinish(data)
    # Array fields should be cleaned to first element
    assert race.avg_power == 150
    assert race.avg_wkg == '3.0'
    assert race.weight == '50.0'
    # Field names should be mapped (zid→zwift_id)
    assert race.zwift_id == '123'
    assert race.time == 3600.5
    assert race.np == 160
    # Old field names should NOT be accessible after renaming
    with pytest.raises(AttributeError):
      _ = race.zid

  def test_init_handles_non_array_values(self):
    """Test that non-array values in array fields are preserved."""
    data = {
      'avg_power': 150,  # Not an array
      'weight': None,  # None value
      'time': [],  # Empty array - but time is always 0.0 due to conversion
    }
    race = ZPRaceFinish(data)
    # Non-array values should be preserved as-is
    assert race.avg_power == 150
    assert race.weight is None
    # Empty arrays in time should be converted to 0.0 due to time field conversion
    assert race.time == 0.0


class TestRaceFinishAttributeAccess:
  """Test attribute-style access to race data."""

  def test_getattr_returns_field_value(self, race_finish):
    """Test accessing fields via attributes."""
    assert race_finish.event_title == 'Stage 1: Fresh Outta 25: Prospect Park Loop'
    assert race_finish.position == 112
    assert race_finish.zwift_id == '5230175'  # Field alias: zwid -> zwift_id

  def test_getattr_returns_cleaned_values(self, race_finish):
    """Test that array fields are cleaned to scalar values."""
    # avg_power and avg_wkg should be cleaned from [value, flag] to just value
    assert race_finish.avg_power == 123
    assert race_finish.avg_wkg == '2.5'

  def test_getattr_missing_field_raises_attribute_error(self, race_finish):
    """Test accessing non-existent field raises AttributeError."""
    with pytest.raises(AttributeError) as exc_info:
      _ = race_finish.nonexistent_field
    assert 'nonexistent_field' in str(exc_info.value)

  def test_getattr_private_field_raises_attribute_error(self, race_finish):
    """Test accessing private fields raises AttributeError."""
    with pytest.raises(AttributeError):
      _ = race_finish._nonexistent


class TestRaceFinishDictAccess:
  """Test dictionary-style access to race data."""

  def test_getitem_returns_field_value(self, race_finish):
    """Test accessing fields via dictionary syntax."""
    assert race_finish['event_title'] == 'Stage 1: Fresh Outta 25: Prospect Park Loop'
    assert race_finish['position'] == 112
    assert race_finish['zwift_id'] == '5230175'  # Field alias: zwid -> zwift_id

  def test_getitem_missing_field_raises_key_error(self, race_finish):
    """Test accessing non-existent field raises KeyError."""
    with pytest.raises(KeyError):
      _ = race_finish['nonexistent_field']

  def test_getitem_and_getattr_return_same_value(self, race_finish):
    """Test that dict and attribute access return the same value."""
    assert race_finish['event_title'] == race_finish.event_title
    assert race_finish['position'] == race_finish.position
    assert race_finish['avg_power'] == race_finish.avg_power


class TestRaceFinishRepr:
  """Test string representation."""

  def test_repr_contains_all_fields(self, race_finish):
    """Test repr shows all race data fields."""
    repr_str = repr(race_finish)
    assert 'RaceFinish' in repr_str
    # Check that all fields from sample data are present (using mapped names)
    assert "zwift_id='5230175'" in repr_str
    assert 'position=112' in repr_str
    assert 'event_title=' in repr_str
    assert 'Prospect Park Loop' in repr_str
    assert 'avg_power=123' in repr_str
    # Verify old field name is not in repr (it was aliased to zwift_id)
    assert 'zwid=' not in repr_str

  def test_repr_is_single_line(self, race_finish):
    """Test repr returns a single line."""
    repr_str = repr(race_finish)
    # Should be one line (no newlines except possibly at end)
    assert repr_str.count('\n') == 0

  def test_repr_handles_empty_data(self):
    """Test repr with completely empty data."""
    race = ZPRaceFinish({})
    repr_str = repr(race)
    # Empty race includes default converted fields
    assert (
      repr_str
      == "ZPRaceFinish(category='', category_women='', time=0.0, time_hms='', time_gun=0.0, time_gun_hms='', event_date='')"
    )

  def test_str_contains_all_fields(self, race_finish):
    """Test str shows all race data fields in multi-line format."""
    str_repr = str(race_finish)
    assert 'ZPRaceFinish(' in str_repr
    # Check for multiple lines
    assert '\n' in str_repr
    # Check that fields are present (using mapped names)
    assert "zwift_id='5230175'" in str_repr
    assert 'position=112' in str_repr
    assert 'event_title=' in str_repr
    assert 'avg_power=123' in str_repr

  def test_str_is_multiline(self, race_finish):
    """Test str returns multiple lines."""
    str_repr = str(race_finish)
    lines = str_repr.split('\n')
    # Should have opening line, multiple data lines, and closing line
    assert len(lines) > 3
    assert lines[0] == 'ZPRaceFinish('
    assert lines[-1] == ')'

  def test_str_handles_empty_data(self):
    """Test str with completely empty data."""
    race = ZPRaceFinish({})
    str_repr = str(race)
    # Empty race includes default converted fields
    assert (
      str_repr
      == "ZPRaceFinish(\n  category='',\n  category_women='',\n  time=0.0,\n  time_hms='',\n  time_gun=0.0,\n  time_gun_hms='',\n  event_date='',\n)"
    )


class TestRaceFinishAsdict:
  """Test serialization back to dictionary."""

  def test_asdict_returns_cleaned_data(self, race_finish):
    """Test asdict returns the cleaned dictionary."""
    result = race_finish.asdict()
    # Should return cleaned data (array fields converted to scalars)
    assert result['avg_power'] == 123
    assert result['avg_wkg'] == '2.5'
    # Other fields should use mapped names (zid→zwift_id, pos→position)
    assert result['zwift_id'] == '5230175'
    assert result['position'] == 112

  def test_asdict_returns_copy_reference(self, race_finish):
    """Test that asdict returns reference to internal data."""
    result = race_finish.asdict()
    # Should be same reference (not a copy)
    assert result is race_finish._data

  def test_asdict_with_empty_data(self):
    """Test asdict with empty race data."""
    race = ZPRaceFinish({})
    # Empty race includes default converted fields
    assert race.asdict() == {
      'category': '',
      'category_women': '',
      'time': 0.0,
      'time_hms': '',
      'time_gun': 0.0,
      'time_gun_hms': '',
      'event_date': '',
    }


class TestRaceFinishWithRealData:
  """Test RaceFinish with real fixture data."""

  @pytest.fixture
  def real_race_data(self):
    """Load real race data from fixture file."""
    fixture_path = Path(__file__).parent.parent.parent / 'tmp' / '7574336_all.json'
    if not fixture_path.exists():
      pytest.skip('Fixture file not available')

    with open(fixture_path) as f:
      data = json.load(f)

    if not data.get('data') or len(data['data']) == 0:
      pytest.skip('No race data in fixture')

    return data['data'][0]

  def test_real_race_data_has_expected_fields(self, real_race_data):
    """Test that real race data has expected fields."""
    race = ZPRaceFinish(real_race_data)

    # Check core fields exist (using aliased names: zid→zwift_id, pos→position)
    assert hasattr(race, 'zwift_id')
    assert hasattr(race, 'event_title')
    assert hasattr(race, 'position')
    # Old field name 'zwid' should NOT exist (aliased to zwift_id)
    assert not hasattr(race, 'zwid')

  def test_real_race_data_attribute_access(self, real_race_data):
    """Test attribute access with real data."""
    race = ZPRaceFinish(real_race_data)

    # Should not raise
    _ = race.event_title
    _ = race.position
    _ = race.avg_power

  def test_real_race_data_serialization(self, real_race_data):
    """Test that real data can be serialized back."""
    race = ZPRaceFinish(real_race_data)
    result = race.asdict()

    # Should be able to serialize to JSON
    json_str = json.dumps(result)
    assert len(json_str) > 0
