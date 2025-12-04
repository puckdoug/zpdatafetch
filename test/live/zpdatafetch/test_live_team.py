"""Live tests for Team data fetching.

These tests make real API calls to zwiftpower.com and require valid credentials.
Run with: pytest --live
"""

import pytest

from zpdatafetch.team import Team


@pytest.mark.live
def test_live_team_fetch_single_id(valid_team_id):
  """Test fetching single team ID via sync interface."""
  team = Team()
  result = team.fetch(valid_team_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_team_id in result
  assert isinstance(result[valid_team_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(team.raw, dict)
  assert valid_team_id in team.raw
  assert isinstance(team.raw[valid_team_id], str)

  # Validate processed attribute
  assert isinstance(team.processed, dict)
  assert valid_team_id in team.processed
  assert isinstance(team.processed[valid_team_id], dict)

  # Validate data is non-empty
  assert len(team.raw[valid_team_id]) > 0


@pytest.mark.live
def test_live_team_fetch_multiple_ids(valid_team_id):
  """Test fetching multiple team IDs via sync interface."""
  team = Team()
  # Use same ID twice to test multiple ID handling
  result = team.fetch(valid_team_id, valid_team_id + 1)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) >= 1  # At least one should succeed

  # Validate first team ID is present
  assert valid_team_id in result
  assert isinstance(result[valid_team_id], dict)

  # Validate raw data
  assert valid_team_id in team.raw
  assert isinstance(team.raw[valid_team_id], str)
  assert len(team.raw[valid_team_id]) > 0

  # Validate processed data
  assert valid_team_id in team.processed
  assert isinstance(team.processed[valid_team_id], dict)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_team_afetch_single_id(valid_team_id):
  """Test fetching single team ID via async interface."""
  team = Team()
  result = await team.afetch(valid_team_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_team_id in result
  assert isinstance(result[valid_team_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(team.raw, dict)
  assert valid_team_id in team.raw
  assert isinstance(team.raw[valid_team_id], str)

  # Validate processed attribute
  assert isinstance(team.processed, dict)
  assert valid_team_id in team.processed
  assert isinstance(team.processed[valid_team_id], dict)

  # Validate data is non-empty
  assert len(team.raw[valid_team_id]) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_team_afetch_multiple_ids(valid_team_id):
  """Test fetching multiple team IDs via async interface."""
  team = Team()
  # Use same ID twice to test multiple ID handling
  result = await team.afetch(valid_team_id, valid_team_id + 1)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) >= 1  # At least one should succeed

  # Validate first team ID is present
  assert valid_team_id in result
  assert isinstance(result[valid_team_id], dict)

  # Validate raw data
  assert valid_team_id in team.raw
  assert isinstance(team.raw[valid_team_id], str)
  assert len(team.raw[valid_team_id]) > 0

  # Validate processed data
  assert valid_team_id in team.processed
  assert isinstance(team.processed[valid_team_id], dict)
