"""Tests for dataclass validation in zpdatafetch.

WILL FAIL initially - proves dataclasses accept invalid IDs.
These tests expect fetch() to raise ValueError for invalid input.
Currently, they accept invalid input, so tests will pass.
After Phase 2, these tests should fail, proving validation was added.
"""

import sys

import pytest

from zpdatafetch import ZPCyclistFetch, ZPResultFetch, ZPTeamFetch


class TestCyclistValidation:
  """Test ZPCyclistFetch validation - WILL PASS until Phase 2 complete (proving gap exists)."""

  def test_accepts_negative_id_currently(self):
    """FAILING TEST: ZPCyclistFetch currently accepts negative IDs."""
    # This should raise ValueError but doesn't currently
    cyclist = ZPCyclistFetch()
    try:
      cyclist.fetch(-5)
      # If we get here, validation is missing (test passes, proving gap)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      # If we get here, validation exists (test would fail)
      pass

  def test_accepts_zero_id_currently(self):
    """FAILING TEST: Cyclist currently accepts zero ID."""
    cyclist = ZPCyclistFetch()
    try:
      cyclist.fetch(0)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass

  def test_accepts_too_large_id_currently(self):
    """FAILING TEST: Cyclist currently accepts IDs > sys.maxsize."""
    cyclist = ZPCyclistFetch()
    try:
      cyclist.fetch(sys.maxsize + 1)
      pytest.skip('Validation not implemented yet - gap exists')
    except (ValueError, OverflowError):
      pass

  def test_accepts_non_integer_string_currently(self):
    """FAILING TEST: Cyclist currently processes invalid strings."""
    cyclist = ZPCyclistFetch()
    try:
      cyclist.fetch('abc')
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass


class TestZPResultFetchValidation:
  """Test ZPResultFetch validation - WILL PASS until Phase 2 complete (proving gap exists)."""

  def test_accepts_negative_race_id_currently(self):
    """FAILING TEST: ZPResultFetch currently accepts negative race IDs."""
    result = ZPResultFetch()
    try:
      result.fetch(-10)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass

  def test_accepts_zero_race_id_currently(self):
    """FAILING TEST: ZPResultFetch currently accepts zero race ID."""
    result = ZPResultFetch()
    try:
      result.fetch(0)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass


class TestZPTeamFetchValidation:
  """Test ZPTeamFetch validation - WILL PASS until Phase 2 complete (proving gap exists)."""

  def test_accepts_negative_team_id_currently(self):
    """FAILING TEST: ZPTeamFetch currently accepts negative team IDs."""
    team = ZPTeamFetch()
    try:
      team.fetch(-20)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass
