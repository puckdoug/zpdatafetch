"""Unit tests for zr_utils module functions."""

from zrdatafetch.zr_utils import safe_float, safe_int


class TestSafeFloat:
  """Tests for safe_float function."""

  def test_none_uses_default(self) -> None:
    """None should return the default."""
    assert safe_float(None) == 0.0
    assert safe_float(None, default=9.9) == 9.9

  def test_numeric_passthrough(self) -> None:
    """Numeric inputs should convert directly."""
    assert safe_float(3.14) == 3.14
    assert safe_float(42) == 42.0

  def test_numeric_string(self) -> None:
    """Plain numeric strings should parse."""
    assert safe_float('3.14') == 3.14

  def test_strips_us_thousands_separator(self) -> None:
    """US-formatted float strings (e.g. '7,200.0') must parse to 7200.0."""
    assert safe_float('7,200.0') == 7200.0

  def test_strips_multiple_thousands_separators(self) -> None:
    """Multiple comma separators (e.g. '1,234,567.89') must parse."""
    assert safe_float('1,234,567.89') == 1234567.89

  def test_invalid_uses_default(self) -> None:
    """Unparseable strings fall back to the default."""
    assert safe_float('not_a_number') == 0.0
    assert safe_float('not_a_number', default=9.9) == 9.9


class TestSafeInt:
  """Tests for safe_int function."""

  def test_none_uses_default(self) -> None:
    """None should return the default."""
    assert safe_int(None) == 0
    assert safe_int(None, default=99) == 99

  def test_numeric_passthrough(self) -> None:
    """Numeric inputs should convert directly."""
    assert safe_int(42) == 42

  def test_numeric_string(self) -> None:
    """Plain numeric strings should parse."""
    assert safe_int('42') == 42

  def test_strips_us_thousands_separator(self) -> None:
    """US-formatted int strings (e.g. '1,000') must parse to 1000."""
    assert safe_int('1,000') == 1000

  def test_strips_multiple_thousands_separators(self) -> None:
    """Multiple comma separators (e.g. '12,345,678') must parse."""
    assert safe_int('12,345,678') == 12345678

  def test_invalid_uses_default(self) -> None:
    """Unparseable strings fall back to the default."""
    assert safe_int('not_a_number') == 0
    assert safe_int('not_a_number', default=99) == 99
