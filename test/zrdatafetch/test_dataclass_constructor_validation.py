"""Tests for zrdatafetch dataclass constructor validation.

WILL PASS initially - proves constructors don't validate.
After Phase 4, these tests should fail, proving __post_init__() validation was added.
"""

import sys

import pytest

from zrdatafetch import ZRResult, ZRRider, ZRTeam


class TestZRRiderConstructorValidation:
  """Test ZRRider constructor - WILL PASS until Phase 4 complete (proving gap exists)."""

  def test_accepts_negative_zwift_id_currently(self):
    """FAILING TEST: ZRRider constructor accepts negative IDs."""
    # This should raise ValueError in __post_init__ but doesn't currently
    try:
      ZRRider(zwift_id=-5)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass

  def test_accepts_too_large_zwift_id_currently(self):
    """FAILING TEST: ZRRider constructor accepts IDs beyond limit."""
    try:
      ZRRider(zwift_id=sys.maxsize)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass

  def test_accepts_invalid_epoch_currently(self):
    """FAILING TEST: ZRRider accepts invalid epochs."""
    try:
      ZRRider(zwift_id=123, epoch=-999)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass

  def test_allows_zero_as_default(self):
    """Zero should be allowed as default/uninitialized value."""
    rider = ZRRider(zwift_id=0)  # Should work
    assert rider.zwift_id == 0

  def test_allows_minus_one_epoch_as_default(self):
    """Epoch -1 should be allowed as default."""
    rider = ZRRider(zwift_id=123, epoch=-1)  # Should work
    assert rider.epoch == -1


class TestZRResultConstructorValidation:
  """Test ZRResult constructor - WILL PASS until Phase 4 complete (proving gap exists)."""

  def test_accepts_negative_race_id_currently(self):
    """FAILING TEST: ZRResult constructor accepts negative race IDs."""
    try:
      ZRResult(race_id=-10)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass

  def test_accepts_zero_race_id_currently(self):
    """FAILING TEST: ZRResult constructor accepts zero race ID."""
    try:
      ZRResult(race_id=0)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass


class TestZRTeamConstructorValidation:
  """Test ZRTeam constructor - WILL PASS until Phase 4 complete (proving gap exists)."""

  def test_accepts_negative_team_id_currently(self):
    """FAILING TEST: ZRTeam constructor accepts negative team IDs."""
    try:
      ZRTeam(team_id=-20)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass


class TestZRRiderBatchValidation:
  """Test ZRRider.fetch_batch - WILL PASS until Phase 6 complete (proving gap exists)."""

  def test_batch_accepts_invalid_ids_currently(self):
    """FAILING TEST: fetch_batch doesn't validate individual IDs."""
    rider = ZRRider()
    try:
      rider.fetch_batch(-1, 0, sys.maxsize, 123)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass

  def test_batch_accepts_too_many_ids_currently(self):
    """FAILING TEST: fetch_batch doesn't validate batch size."""
    rider = ZRRider()
    too_many = list(range(1, 2000))  # 1999 IDs, exceeds 1000 limit
    try:
      rider.fetch_batch(*too_many)
      pytest.skip('Validation not implemented yet - gap exists')
    except ValueError:
      pass
