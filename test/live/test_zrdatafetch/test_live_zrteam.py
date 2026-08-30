"""Live tests for ZRTeamFetch that make real API calls to zwiftracing.app."""

import pytest

from zrdatafetch import ZRTeamFetch


@pytest.mark.live
def test_live_zrteam_fetch_single_id(valid_team_id):
  """Test synchronous fetch of a single team ID."""
  fetcher = ZRTeamFetch()
  teams = fetcher.fetch(valid_team_id)

  assert valid_team_id in teams
  team = teams[valid_team_id]

  # Verify parsed data
  assert team.team_id == valid_team_id
  assert team.team_name is not None
  assert isinstance(team.team_name, str)
  assert len(team) >= 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrteam_afetch_single_id(valid_team_id):
  """Test asynchronous fetch of a single team ID."""
  fetcher = ZRTeamFetch()
  teams = await fetcher.afetch(valid_team_id)

  assert valid_team_id in teams
  team = teams[valid_team_id]

  # Verify parsed data
  assert team.team_id == valid_team_id
  assert team.team_name is not None
  assert isinstance(team.team_name, str)
  assert len(team) >= 0
