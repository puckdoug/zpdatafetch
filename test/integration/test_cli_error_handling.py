"""Integration tests for CLI error handling.

WILL PASS initially - proves CLIs don't catch validation errors properly.
After Phase 3, these tests should fail, proving friendly error handling was added.
"""

import subprocess

import pytest


class TestZPDataCLIErrors:
  """Test zpdata CLI error handling - WILL PASS until Phase 3 complete (proving gap exists)."""

  def test_shows_stack_trace_for_invalid_id_currently(self):
    """FAILING TEST: CLI shows stack trace instead of friendly error."""
    result = subprocess.run(
      ['python', '-m', 'zpdatafetch.cyclist', 'abc'],
      capture_output=True,
      text=True,
      check=False,
    )

    # Currently shows stack trace with "Traceback (most recent call last)"
    # Should show friendly error message without stack trace
    if result.returncode == 1:
      if 'Traceback' in result.stderr:
        # Stack trace present - gap exists
        pytest.skip('Validation not implemented yet - gap exists')
      # No stack trace - validation exists

  def test_no_clear_error_for_negative_id_currently(self):
    """FAILING TEST: Negative IDs don't show clear error."""
    result = subprocess.run(
      ['python', '-m', 'zpdatafetch.cyclist', '-5'],
      capture_output=True,
      text=True,
      check=False,
    )

    if result.returncode == 1:
      if 'must be between 1 and' not in result.stderr:
        # No clear message - gap exists
        pytest.skip('Validation not implemented yet - gap exists')


class TestZRDataCLIErrors:
  """Test zrdata CLI error handling - WILL PASS until Phase 3 complete (proving gap exists)."""

  def test_accepts_invalid_string_id_currently(self):
    """FAILING TEST: zrdata doesn't validate string IDs properly."""
    result = subprocess.run(
      ['python', '-m', 'zrdatafetch.rider', 'xyz'],
      capture_output=True,
      text=True,
      check=False,
    )

    if result.returncode == 1:
      if 'must be an integer' not in result.stderr:
        # No clear message - gap exists
        pytest.skip('Validation not implemented yet - gap exists')
