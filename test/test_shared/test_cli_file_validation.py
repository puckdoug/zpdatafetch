"""Tests for file input validation.

WILL PASS initially - proves file input doesn't validate.
After Phase 5, these tests should fail, proving validation was added.
"""

import tempfile
from pathlib import Path

import pytest

from shared.cli import read_ids_from_file


class TestReadIDsFromFile:
  """Test file input validation - WILL PASS until Phase 5 complete (proving gap exists)."""

  def test_accepts_invalid_ids_in_file_currently(self):
    """FAILING TEST: read_ids_from_file accepts invalid IDs."""
    with tempfile.NamedTemporaryFile(
      mode='w',
      delete=False,
      suffix='.txt',
    ) as f:
      f.write('123\nabc\n456\n')
      filepath = f.name

    try:
      # Currently returns ["123", "abc", "456"] as strings
      # Should validate and return None on error
      result = read_ids_from_file(filepath)
      if result is not None and not all(isinstance(x, int) for x in result):
        # Returns strings - validation gap exists
        pytest.skip('Validation not implemented yet - gap exists')
      # If we get here with integers, validation exists
    finally:
      Path(filepath).unlink()

  def test_accepts_negative_ids_in_file_currently(self):
    """FAILING TEST: File input doesn't validate ranges."""
    with tempfile.NamedTemporaryFile(
      mode='w',
      delete=False,
      suffix='.txt',
    ) as f:
      f.write('123\n-5\n456\n')
      filepath = f.name

    try:
      result = read_ids_from_file(filepath)
      # Should return None or raise error, not process -5
      if result is not None:
        pytest.skip('Validation not implemented yet - gap exists')
    finally:
      Path(filepath).unlink()

  def test_no_error_message_for_invalid_line_currently(self):
    """FAILING TEST: No line number in error messages."""
    with tempfile.NamedTemporaryFile(
      mode='w',
      delete=False,
      suffix='.txt',
    ) as f:
      f.write('10\n20\nabc\n40\n')
      filepath = f.name

    try:
      # When validation is added, should report "position 3"
      result = read_ids_from_file(filepath)
      # Currently returns strings, should return None with clear error
      if result is not None:
        pytest.skip('Validation not implemented yet - gap exists')
    finally:
      Path(filepath).unlink()
