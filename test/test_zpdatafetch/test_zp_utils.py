"""Unit tests for zp_utils module functions."""

from zpdatafetch.zp_utils import (
  convert_gender,
  convert_timestamp_to_iso8601,
  extract_numeric,
  extract_value,
  format_time_hms,
  set_rider_category,
)


class TestSetRiderCategory:
  """Tests for set_rider_category function."""

  def test_division_0_returns_empty_string(self) -> None:
    """Division 0 should map to empty string (no division)."""
    assert set_rider_category(0) == ''

  def test_division_10_returns_a(self) -> None:
    """Division 10 should map to 'A'."""
    assert set_rider_category(10) == 'A'

  def test_division_20_returns_b(self) -> None:
    """Division 20 should map to 'B'."""
    assert set_rider_category(20) == 'B'

  def test_division_30_returns_c(self) -> None:
    """Division 30 should map to 'C'."""
    assert set_rider_category(30) == 'C'

  def test_division_40_returns_d(self) -> None:
    """Division 40 should map to 'D'."""
    assert set_rider_category(40) == 'D'

  def test_unknown_division_returns_string(self) -> None:
    """Unknown division should return string representation."""
    assert set_rider_category(50) == '50'
    assert set_rider_category(99) == '99'


class TestConvertGender:
  """Tests for convert_gender function."""

  def test_male_code_1_returns_male(self) -> None:
    """Gender code 1 should map to 'male'."""
    assert convert_gender(1) == 'male'

  def test_male_code_0_returns_female(self) -> None:
    """Gender code 0 should map to 'female'."""
    assert convert_gender(0) == 'female'

  def test_male_string_m_returns_male(self) -> None:
    """Gender string 'm' should map to 'male'."""
    assert convert_gender('m') == 'male'
    assert convert_gender('M') == 'male'

  def test_female_string_f_returns_female(self) -> None:
    """Gender string 'f' should map to 'female'."""
    assert convert_gender('f') == 'female'
    assert convert_gender('F') == 'female'

  def test_unknown_gender_code_returns_empty_string(self) -> None:
    """Unknown gender code should return empty string."""
    assert convert_gender(2) == ''
    assert convert_gender(-1) == ''
    assert convert_gender('x') == ''
    assert convert_gender('') == ''


class TestFormatTimeHms:
  """Tests for format_time_hms function."""

  def test_zero_returns_empty_string(self) -> None:
    """Zero seconds should return empty string."""
    assert format_time_hms(0) == ''

  def test_format_seconds_only(self) -> None:
    """Seconds only should format correctly."""
    assert format_time_hms(45.5) == '00:00:45.500'

  def test_format_minutes_and_seconds(self) -> None:
    """Minutes and seconds should format correctly."""
    assert format_time_hms(125.25) == '00:02:05.250'

  def test_format_hours_minutes_seconds(self) -> None:
    """Hours, minutes, and seconds should format correctly."""
    assert format_time_hms(3661.123) == '01:01:01.123'

  def test_format_multiple_hours(self) -> None:
    """Multiple hours should format correctly."""
    assert format_time_hms(7323.5) == '02:02:03.500'

  def test_format_none_returns_empty_string(self) -> None:
    """None value should return empty string."""
    assert format_time_hms(None) == ''

  def test_format_false_returns_empty_string(self) -> None:
    """False value should return empty string."""
    assert format_time_hms(False) == ''


class TestConvertTimestampToIso8601:
  """Tests for convert_timestamp_to_iso8601 function."""

  def test_zero_timestamp_returns_empty_string(self) -> None:
    """Zero timestamp should return empty string."""
    assert convert_timestamp_to_iso8601(0) == ''

  def test_none_timestamp_returns_empty_string(self) -> None:
    """None timestamp should return empty string."""
    assert convert_timestamp_to_iso8601(None) == ''

  def test_string_timestamp_returned_as_is(self) -> None:
    """String timestamp should be returned as-is."""
    iso_str = '2025-12-03T22:10:00Z'
    assert convert_timestamp_to_iso8601(iso_str) == iso_str

  def test_numeric_timestamp_conversion(self) -> None:
    """Numeric timestamp should be converted to ISO-8601 UTC format."""
    # Unix timestamp for 2025-01-20 12:00:00 UTC
    timestamp = 1737371400.0
    result = convert_timestamp_to_iso8601(timestamp)
    # Result should be in ISO-8601 format ending with Z
    assert result.endswith('Z')
    assert 'T' in result
    assert '2025-01-20' in result

  def test_invalid_timestamp_returns_empty_string(self) -> None:
    """Invalid timestamp should return empty string."""
    # Very large timestamp that would cause OSError
    assert convert_timestamp_to_iso8601(999999999999999999.0) == ''


class TestExtractValue:
  """Tests for extract_value function."""

  def test_extract_scalar_value(self) -> None:
    """Scalar value should be returned as-is."""
    assert extract_value(42) == 42
    assert extract_value('test') == 'test'

  def test_extract_first_element_from_list(self) -> None:
    """First element should be extracted from list."""
    assert extract_value([42, 0]) == 42
    assert extract_value(['value', 'flag']) == 'value'

  def test_extract_from_single_element_list(self) -> None:
    """Single element list should return that element."""
    assert extract_value([42]) == 42

  def test_extract_from_empty_list_returns_empty_list(self) -> None:
    """Empty list should be returned as-is (not converted)."""
    assert extract_value([], default=99) == []
    assert extract_value([]) == []

  def test_extract_none_uses_default(self) -> None:
    """None value should use default."""
    assert extract_value(None, default=99) == 99
    assert extract_value(None, default='default') == 'default'

  def test_extract_default_none_by_default(self) -> None:
    """Default should be None if not specified."""
    assert extract_value(None) is None


class TestExtractNumeric:
  """Tests for extract_numeric function."""

  def test_extract_int_from_scalar(self) -> None:
    """Scalar int should be converted."""
    assert extract_numeric(42, int, 0) == 42

  def test_extract_int_from_list(self) -> None:
    """First element of list should be converted to int."""
    assert extract_numeric([42, 0], int, 0) == 42

  def test_extract_float_from_scalar(self) -> None:
    """Scalar float should be converted."""
    assert extract_numeric(3.14, float, 0.0) == 3.14

  def test_extract_float_from_list(self) -> None:
    """First element of list should be converted to float."""
    assert extract_numeric([3.14, 0], float, 0.0) == 3.14

  def test_extract_int_from_string(self) -> None:
    """String should be converted to int if possible."""
    assert extract_numeric('42', int, 0) == 42

  def test_extract_float_from_string(self) -> None:
    """String should be converted to float if possible."""
    assert extract_numeric('3.14', float, 0.0) == 3.14

  def test_extract_invalid_int_uses_default(self) -> None:
    """Invalid int conversion should use default."""
    assert extract_numeric('not_a_number', int, 99) == 99

  def test_extract_invalid_float_uses_default(self) -> None:
    """Invalid float conversion should use default."""
    assert extract_numeric('not_a_number', float, 9.9) == 9.9

  def test_extract_none_uses_default(self) -> None:
    """None value should use default."""
    assert extract_numeric(None, int, 0) == 0
    assert extract_numeric(None, float, 0.0) == 0.0

  def test_extract_empty_list_uses_default(self) -> None:
    """Empty list should use default."""
    assert extract_numeric([], int, 99) == 99
    assert extract_numeric([], float, 9.9) == 9.9
