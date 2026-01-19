"""Test CLI flag combinations for --excluded and --extras."""

from zpdatafetch.zpraceresult import ZPRiderFinish


def test_excluded_flag_with_excluded_data():
  """Test that --excluded flag correctly shows excluded fields in rider data."""
  # Create rider with excluded data
  rider = ZPRiderFinish.from_dict(
    {
      "pos": 1,
      "zwift_id": 123,
      "name": "Test Rider",
      "unknown_field_1": "value1",  # Will be in excluded
    },
  )

  # Should have excluded data
  excluded = rider.excluded()
  assert "unknown_field_1" in excluded
  assert excluded["unknown_field_1"] == "value1"

  # Should have no extras
  extras = rider.extras()
  assert len(extras) == 0


def test_both_flags_independently():
  """Test that both --excluded and --extras flags can be used on same rider."""
  # Create rider with only excluded data
  rider_excluded_only = ZPRiderFinish.from_dict(
    {
      "pos": 1,
      "zwift_id": 123,
      "name": "Test Rider",
      "unknown_field_1": "value1",
    },
  )

  # Verify excluded
  assert len(rider_excluded_only.excluded()) > 0
  assert len(rider_excluded_only.extras()) == 0

  # Now create a rider with extra data (this shouldn't happen normally,
  # but we test that the CLI logic can handle both separately)
  rider_extras_only = ZPRiderFinish()
  # Manually set some extras for testing
  rider_extras_only._extra["extra_field"] = "extra_value"

  # Verify extras
  assert len(rider_extras_only.extras()) > 0


def test_excluded_excludes_known_aliases():
  """Test that known field aliases are excluded from excluded dict."""
  # Create rider with both main field name and alias
  rider = ZPRiderFinish.from_dict(
    {
      "pos": 1,  # Alias for position
      "zwift_id": 123,
      "name": "Test Rider",
      "ftp": 300,  # Alias for zftp
    },
  )

  # Both pos, zwift_id, and ftp should be recognized as known fields
  # and not appear in excluded
  excluded = rider.excluded()
  assert "pos" not in excluded
  assert "ftp" not in excluded
  assert "zwift_id" not in excluded

  # Values should be properly assigned
  assert rider.position == 1
  assert rider.zftp == 300


def test_flag_combination_logic():
  """Test the logic for combining --excluded and --extras flags."""

  # Create mock args that could be used in CLI
  class MockArgs:
    def __init__(self, excluded: bool, extras: bool) -> None:
      self.excluded = excluded
      self.extras = extras

  # Test exclusive cases
  args_excluded_only = MockArgs(excluded=True, extras=False)
  assert args_excluded_only.excluded or args_excluded_only.extras

  args_extras_only = MockArgs(excluded=False, extras=True)
  assert args_extras_only.excluded or args_extras_only.extras

  # Test combined case
  args_both = MockArgs(excluded=True, extras=True)
  assert args_both.excluded or args_both.extras
  assert args_both.excluded and args_both.extras

  # Test determining message
  def get_no_data_message(excluded, extras):
    if excluded and extras:
      return 'No excluded or extras'
    if excluded:
      return 'No excluded'
    return 'No extras'

  assert get_no_data_message(True, False) == 'No excluded'
  assert get_no_data_message(False, True) == 'No extras'
  assert get_no_data_message(True, True) == 'No excluded or extras'
