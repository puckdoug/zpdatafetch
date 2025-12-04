"""Live tests for ZRTeam that make real API calls to zwiftracing.app."""

import pytest

from zrdatafetch.zrteam import ZRTeam


@pytest.mark.live
def test_live_zrteam_fetch_single_id(valid_team_id):
  """Test synchronous fetch of a single team ID."""
  team = ZRTeam(team_id=valid_team_id)
  team.fetch()

  # Verify raw data exists and is a string
  assert team._raw is not None
  assert isinstance(team._raw, str)
  assert len(team._raw) > 0

  # Verify parsed data
  assert team.team_id == valid_team_id
  assert team.team_name is not None
  assert isinstance(team.team_name, str)
  assert team.riders is not None
  assert isinstance(team.riders, list)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrteam_afetch_single_id(valid_team_id):
  """Test asynchronous fetch of a single team ID."""
  team = ZRTeam(team_id=valid_team_id)
  await team.afetch()

  # Verify raw data exists and is a string
  assert team._raw is not None
  assert isinstance(team._raw, str)
  assert len(team._raw) > 0

  # Verify parsed data
  assert team.team_id == valid_team_id
  assert team.team_name is not None
  assert isinstance(team.team_name, str)
  assert team.riders is not None
  assert isinstance(team.riders, list)
