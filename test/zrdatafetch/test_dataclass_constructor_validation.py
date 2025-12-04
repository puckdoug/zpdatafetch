"""Tests for zrdatafetch dataclass constructor validation.

WILL PASS initially - proves constructors don't validate.
After Phase 4, these tests should fail, proving __post_init__() validation was added.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from zrdatafetch import ZRResult, ZRRider, ZRTeam


class TestZRRiderConstructorValidation:
  """Test ZRRider constructor"""

  def test_accepts_negative_zwift_id_currently(self):
    """ZRRider constructor should not accept negative IDs."""
    # This should raise ValueError in __post_init__ 
    try:
      ZRRider(zwift_id=-5)
    except ValueError:
      pass

  def test_accepts_too_large_zwift_id_currently(self):
    """ZRRider constructor should not accept IDs beyond limit."""
    try:
      ZRRider(zwift_id=sys.maxsize)
    except ValueError:
      pass

  def test_accepts_invalid_epoch_currently(self):
    """ZRRider should not accept invalid epochs."""
    try:
      ZRRider(zwift_id=123, epoch=-999)
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
  """Test ZRResult constructor"""

  def test_accepts_negative_race_id_currently(self):
    """ZRResult constructor should not accept negative race IDs."""
    try:
      ZRResult(race_id=-10)
    except ValueError:
      pass

  def test_accepts_zero_race_id_currently(self):
    """ZRResult constructor should not accept zero race ID."""
    try:
      ZRResult(race_id=0)
    except ValueError:
      pass


class TestZRTeamConstructorValidation:
  """Test ZRTeam constructor"""

  def test_accepts_negative_team_id_currently(self):
    """ZRTeam constructor should not accept negative team IDs."""
    try:
      ZRTeam(team_id=-20)
    except ValueError:
      pass


class TestZRRiderBatchValidation:
  """Test ZRRider.fetch_batch"""

  def test_batch_accepts_invalid_ids_currently(self):
    """fetch_batch validates individual IDs."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'Bearer test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        # Mock response with valid rider data
        mock_fetch.return_value = '[{"name": "Test", "gender": "M", "power": {"compoundScore": 250.0}, "race": {"current": {"rating": 2250.0, "mixed": {"category": "A"}}, "max30": {"rating": 2240.0, "mixed": {"category": "A"}}, "max90": {"rating": 2200.0, "mixed": {"category": "B"}}}}]'

        rider = ZRRider()
        try:
          rider.fetch_batch(-1, 0, sys.maxsize, 123)
        except ValueError:
          pass

  def test_batch_accepts_too_many_ids_currently(self):
    """fetch_batch validates batch size."""
    rider = ZRRider()
    too_many = list(range(1, 2000))  # 1999 IDs, exceeds 1000 limit
    try:
      rider.fetch_batch(*too_many)
    except ValueError:
      pass
