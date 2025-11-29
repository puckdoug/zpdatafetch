"""Tests for shared validation module.

IMPORTANT: These tests will FAIL initially because validation.py doesn't
exist yet. This is intentional - we're proving the validation gaps exist.
"""

import pytest

# This import will fail initially - that's expected
from shared.validation import (
  EPOCH_MAX,
  MAX_BATCH_SIZE,
  RACE_ID_MAX,
  RACE_ID_MIN,
  ZWIFT_ID_MAX,
  ValidationError,
  validate_batch_size,
  validate_epoch,
  validate_id_list,
  validate_race_id,
  validate_team_id,
  validate_zwift_id,
)


class TestValidateZwiftID:
  """Test zwift ID validation - WILL FAIL until Phase 1 complete."""

  def test_valid_id(self):
    """Valid IDs should pass."""
    assert validate_zwift_id(123) == 123
    assert validate_zwift_id('456') == 456
    assert validate_zwift_id(1) == 1  # Min valid
    assert validate_zwift_id(ZWIFT_ID_MAX) == ZWIFT_ID_MAX  # Max valid

  def test_zero_not_allowed_by_default(self):
    """Zero should be rejected by default."""
    with pytest.raises(ValidationError, match='must be between 1 and'):
      validate_zwift_id(0)

  def test_zero_allowed_when_specified(self):
    """Zero should be allowed with allow_zero=True."""
    assert validate_zwift_id(0, allow_zero=True) == 0

  def test_negative_id_rejected(self):
    """Negative IDs should be rejected."""
    with pytest.raises(ValidationError, match='must be between'):
      validate_zwift_id(-1)
    with pytest.raises(ValidationError):
      validate_zwift_id(-999)

  def test_too_large_id_rejected(self):
    """IDs above max should be rejected."""
    with pytest.raises(ValidationError, match='must be between'):
      validate_zwift_id(ZWIFT_ID_MAX + 1)

  def test_non_integer_string_rejected(self):
    """Non-integer strings should be rejected."""
    with pytest.raises(ValidationError, match='must be an integer'):
      validate_zwift_id('abc')
    with pytest.raises(ValidationError):
      validate_zwift_id('12.5')
    with pytest.raises(ValidationError):
      validate_zwift_id('')

  def test_none_rejected(self):
    """None should be rejected."""
    with pytest.raises(ValidationError, match='must be an integer'):
      validate_zwift_id(None)


class TestValidateRaceID:
  """Test race ID validation - WILL FAIL until Phase 1 complete."""

  def test_valid_id(self):
    """Valid race IDs should pass."""
    assert validate_race_id(100) == 100
    assert validate_race_id('200') == 200
    assert validate_race_id(RACE_ID_MIN) == RACE_ID_MIN
    assert validate_race_id(RACE_ID_MAX) == RACE_ID_MAX

  def test_zero_rejected(self):
    """Zero race ID should be rejected."""
    with pytest.raises(ValidationError, match='must be between'):
      validate_race_id(0)

  def test_negative_rejected(self):
    """Negative race IDs should be rejected."""
    with pytest.raises(ValidationError):
      validate_race_id(-5)

  def test_too_large_rejected(self):
    """Race IDs above max should be rejected."""
    with pytest.raises(ValidationError):
      validate_race_id(RACE_ID_MAX + 1)


class TestValidateTeamID:
  """Test team ID validation - WILL FAIL until Phase 1 complete."""

  def test_valid_id(self):
    """Valid team IDs should pass."""
    assert validate_team_id(50) == 50
    assert validate_team_id('75') == 75

  def test_zero_rejected(self):
    """Zero team ID should be rejected."""
    with pytest.raises(ValidationError):
      validate_team_id(0)

  def test_negative_rejected(self):
    """Negative team IDs should be rejected."""
    with pytest.raises(ValidationError):
      validate_team_id(-10)


class TestValidateEpoch:
  """Test epoch validation - WILL FAIL until Phase 1 complete."""

  def test_minus_one_allowed(self):
    """Special value -1 (current epoch) should be allowed."""
    assert validate_epoch(-1) == -1

  def test_zero_allowed(self):
    """Zero epoch should be allowed."""
    assert validate_epoch(0) == 0

  def test_valid_timestamp(self):
    """Valid Unix timestamps should be allowed."""
    assert validate_epoch(1609459200) == 1609459200  # 2021-01-01
    assert validate_epoch(EPOCH_MAX) == EPOCH_MAX

  def test_negative_other_than_minus_one_rejected(self):
    """Negative epochs other than -1 should be rejected."""
    with pytest.raises(ValidationError):
      validate_epoch(-2)
    with pytest.raises(ValidationError):
      validate_epoch(-999)

  def test_too_large_epoch_rejected(self):
    """Epochs beyond 2038 should be rejected."""
    with pytest.raises(ValidationError):
      validate_epoch(EPOCH_MAX + 1)


class TestValidateBatchSize:
  """Test batch size validation - WILL FAIL until Phase 1 complete."""

  def test_valid_batch_size(self):
    """Batch sizes under limit should pass."""
    validate_batch_size(1)
    validate_batch_size(500)
    validate_batch_size(MAX_BATCH_SIZE)

  def test_too_large_batch_rejected(self):
    """Batch sizes over limit should be rejected."""
    with pytest.raises(ValidationError, match='exceeds maximum'):
      validate_batch_size(MAX_BATCH_SIZE + 1)
    with pytest.raises(ValidationError):
      validate_batch_size(5000)


class TestValidateIDList:
  """Test ID list validation - WILL FAIL until Phase 1 complete."""

  def test_valid_zwift_ids(self):
    """Valid zwift ID lists should pass."""
    result = validate_id_list([1, 2, 3], id_type='zwift')
    assert result == [1, 2, 3]

    result = validate_id_list(['10', '20', '30'], id_type='zwift')
    assert result == [10, 20, 30]

  def test_valid_race_ids(self):
    """Valid race ID lists should pass."""
    result = validate_id_list([100, 200], id_type='race')
    assert result == [100, 200]

  def test_valid_team_ids(self):
    """Valid team ID lists should pass."""
    result = validate_id_list([50, 60], id_type='team')
    assert result == [50, 60]

  def test_invalid_id_in_list_rejected_with_position(self):
    """Invalid IDs should report position."""
    with pytest.raises(ValidationError, match='position 2'):
      validate_id_list([1, 'abc', 3], id_type='zwift')

    with pytest.raises(ValidationError, match='position 3'):
      validate_id_list([10, 20, -5], id_type='zwift')

  def test_empty_list(self):
    """Empty lists should return empty."""
    result = validate_id_list([], id_type='zwift')
    assert result == []
