"""Tests for shared.json_helpers module."""

import json

from shared.json_helpers import parse_json_safe


class TestParseJsonSafe:
  """Tests for parse_json_safe function."""

  def test_parse_valid_dict(self):
    """Test parsing valid JSON dict."""
    raw = '{"key": "value", "number": 42}'
    result = parse_json_safe(raw)

    assert isinstance(result, dict)
    assert result == {'key': 'value', 'number': 42}

  def test_parse_valid_list(self):
    """Test parsing valid JSON list."""
    raw = '[1, 2, 3, "four"]'
    result = parse_json_safe(raw)

    assert isinstance(result, list)
    assert result == [1, 2, 3, 'four']

  def test_parse_nested_structure(self):
    """Test parsing complex nested JSON."""
    raw = '{"outer": {"inner": [1, 2, 3]}, "array": [{"id": 1}, {"id": 2}]}'
    result = parse_json_safe(raw)

    assert isinstance(result, dict)
    assert result['outer']['inner'] == [1, 2, 3]
    assert len(result['array']) == 2

  def test_parse_empty_string(self):
    """Test parsing empty string returns empty dict."""
    result = parse_json_safe('')
    assert result == {}

  def test_parse_whitespace_only(self):
    """Test parsing whitespace-only string returns empty dict."""
    result = parse_json_safe('   \n\t  ')
    assert result == {}

  def test_parse_invalid_json(self):
    """Test parsing invalid JSON returns empty dict."""
    raw = 'not valid json {'
    result = parse_json_safe(raw)

    assert result == {}

  def test_parse_malformed_json(self):
    """Test parsing malformed JSON returns empty dict."""
    raw = '{"key": "value",}'  # Trailing comma
    result = parse_json_safe(raw)

    assert result == {}

  def test_parse_with_context(self):
    """Test parsing with context parameter (for logging)."""
    raw = '{"test": true}'
    result = parse_json_safe(raw, context='rider 12345')

    assert result == {'test': True}

  def test_parse_html_error_page(self):
    """Test parsing HTML error page returns empty dict."""
    raw = '<html><body>Error 404</body></html>'
    result = parse_json_safe(raw)

    assert result == {}

  def test_parse_unicode_content(self):
    """Test parsing JSON with Unicode characters."""
    raw = '{"name": "François", "emoji": "🚴"}'
    result = parse_json_safe(raw)

    assert result['name'] == 'François'
    assert result['emoji'] == '🚴'

  def test_parse_large_json(self):
    """Test parsing large JSON structure."""
    # Create a large dict
    large_dict = {f'key_{i}': f'value_{i}' for i in range(1000)}
    raw = json.dumps(large_dict)

    result = parse_json_safe(raw)

    assert isinstance(result, dict)
    assert len(result) == 1000
    assert result['key_0'] == 'value_0'
    assert result['key_999'] == 'value_999'

  def test_parse_json_with_nulls(self):
    """Test parsing JSON containing null values."""
    raw = '{"key": null, "nested": {"value": null}}'
    result = parse_json_safe(raw)

    assert result['key'] is None
    assert result['nested']['value'] is None

  def test_parse_json_with_booleans(self):
    """Test parsing JSON with boolean values."""
    raw = '{"true_val": true, "false_val": false}'
    result = parse_json_safe(raw)

    assert result['true_val'] is True
    assert result['false_val'] is False

  def test_parse_json_with_numbers(self):
    """Test parsing JSON with various number types."""
    raw = '{"int": 42, "float": 3.14, "negative": -10, "scientific": 1.5e10}'
    result = parse_json_safe(raw)

    assert result['int'] == 42
    assert result['float'] == 3.14
    assert result['negative'] == -10
    assert result['scientific'] == 1.5e10
