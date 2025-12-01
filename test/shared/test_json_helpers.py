"""Tests for shared JSON parsing utilities."""

import json

import pytest

from shared.json_helpers import parse_json_safe


class TestParseJsonSafe:
  """Test parse_json_safe function."""

  def test_parse_valid_dict(self):
    """Test parsing valid JSON dict."""
    raw = '{"key": "value", "number": 42}'
    result = parse_json_safe(raw)

    assert result == {"key": "value", "number": 42}
    assert isinstance(result, dict)

  def test_parse_valid_list(self):
    """Test parsing valid JSON list."""
    raw = '[1, 2, 3, "four"]'
    result = parse_json_safe(raw)

    assert result == [1, 2, 3, "four"]
    assert isinstance(result, list)

  def test_parse_nested_structure(self):
    """Test parsing complex nested JSON."""
    raw = '{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}'
    result = parse_json_safe(raw)

    assert result == {
      "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
    }

  def test_parse_empty_string(self):
    """Test parsing empty string returns empty dict."""
    result = parse_json_safe("")

    assert result == {}

  def test_parse_whitespace_only(self):
    """Test parsing whitespace-only string returns empty dict."""
    result = parse_json_safe("   \n\t  ")

    assert result == {}

  def test_parse_invalid_json(self):
    """Test parsing invalid JSON returns empty dict."""
    raw = "not valid json {"
    result = parse_json_safe(raw)

    assert result == {}

  def test_parse_invalid_json_with_context(self):
    """Test parsing invalid JSON logs context."""
    raw = '{"incomplete": '
    result = parse_json_safe(raw, context="test data")

    assert result == {}

  def test_parse_none_value(self):
    """Test parsing None returns empty dict."""
    result = parse_json_safe(None)

    assert result == {}

  def test_parse_preserves_types(self):
    """Test parsing preserves JSON types."""
    raw = '{"string": "text", "int": 123, "float": 45.67, "bool": true, "null": null}'
    result = parse_json_safe(raw)

    assert result["string"] == "text"
    assert result["int"] == 123
    assert result["float"] == 45.67
    assert result["bool"] is True
    assert result["null"] is None

  def test_parse_unicode(self):
    """Test parsing JSON with unicode characters."""
    raw = '{"name": "Kräkel", "symbol": "&#128005;"}'
    result = parse_json_safe(raw)

    assert result["name"] == "Kräkel"
    assert result["symbol"] == "&#128005;"

  def test_parse_empty_dict(self):
    """Test parsing empty dict."""
    raw = "{}"
    result = parse_json_safe(raw)

    assert result == {}

  def test_parse_empty_list(self):
    """Test parsing empty list."""
    raw = "[]"
    result = parse_json_safe(raw)

    assert result == []
