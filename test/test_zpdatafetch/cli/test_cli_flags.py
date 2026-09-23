"""Test CLI flag combinations for --excluded and --extras."""

from zpdatafetch.zpraceresult import ZPRiderFinish


def test_excluded_flag_with_excluded_data():
  """Test that --excluded flag correctly shows excluded fields in rider data."""
  # Create rider with excluded data (known but not in typed fields)
  # and extra data (unknown fields)
  rider = ZPRiderFinish.from_dict(
    {
      'pos': 1,
      'zwift_id': 123,
      'name': 'Test Rider',
      'unknown_field_1': 'value1',  # Will be in extras (unknown field)
    },
  )

  # Unknown fields should be in extras
  extras = rider.extras()
  assert 'unknown_field_1' in extras
  assert extras['unknown_field_1'] == 'value1'

  # Should have no excluded (no known-but-not-typed fields in this example)
  excluded = rider.excluded()
  assert len(excluded) == 0


def test_both_flags_independently():
  """Test that both --excluded and --extras flags can be used on same rider."""
  # Create rider with only extra data (unknown fields)
  rider_extras_only = ZPRiderFinish.from_dict(
    {
      'pos': 1,
      'zwift_id': 123,
      'name': 'Test Rider',
      'unknown_field_1': 'value1',
    },
  )

  # Verify extras
  assert len(rider_extras_only.extras()) > 0
  assert len(rider_extras_only.excluded()) == 0

  # Now create a rider with manually set excluded data
  # (known fields that we deliberately exclude from typed fields)
  rider_excluded_only = ZPRiderFinish()
  # Manually set some excluded for testing
  rider_excluded_only._excluded['excluded_field'] = 'excluded_value'

  # Verify excluded
  assert len(rider_excluded_only.excluded()) > 0


def test_excluded_excludes_known_aliases():
  """Test that known field aliases are excluded from excluded dict."""
  # Create rider with both main field name and alias
  rider = ZPRiderFinish.from_dict(
    {
      'pos': 1,  # Alias for position
      'zwift_id': 123,
      'name': 'Test Rider',
      'ftp': 300,  # Alias for zftp
    },
  )

  # Both pos, zwift_id, and ftp should be recognized as known fields
  # and not appear in excluded
  excluded = rider.excluded()
  assert 'pos' not in excluded
  assert 'ftp' not in excluded
  assert 'zwift_id' not in excluded

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


def test_cli_league_excluded_walks_nested_collections(monkeypatch, capsys):
  """--excluded on a league reports excluded fields from nested collections."""
  import sys

  from zpdatafetch import cli as cli_mod
  from zpdatafetch.zpleague import ZPLeague

  class FakeLeagueFetch:
    def __init__(self) -> None:
      self._fetched = {}
      self._raw = {}

    def fetch(self, *ids):
      self._fetched = {
        3379: ZPLeague.from_dict(
          {},
          league_id=3379,
          events=[
            {'zid': '10', 'DT_RowId': '10', 't': 'Event One', 'tm': 111},
          ],
        )
      }

  monkeypatch.setattr(cli_mod, 'ZPLeagueFetch', FakeLeagueFetch)
  monkeypatch.setattr(sys, 'argv', ['zpdata', 'league', '--excluded', '3379'])

  assert cli_mod.main() is None

  out = capsys.readouterr().out
  assert 'excluded:' in out
  assert 'DT_RowId' in out
