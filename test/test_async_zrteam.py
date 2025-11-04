"""Tests for ZRTeam class with async (afetch) methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.zrteam import ZRTeam


# ===============================================================================
class TestAsyncZRTeamFetch:
  """Test AsyncZRTeam.fetch() method."""

  @pytest.mark.anyio
  async def test_fetch_no_team_id(self):
    """Test fetch with no team_id returns silently."""
    async with AsyncZR_obj() as zr:
      team = ZRTeam()
      team.set_session(zr)
      # Should return without error when team_id is 0
      await team.afetch()
      assert team.team_id == 0

  @pytest.mark.anyio
  async def test_fetch_parses_response(self):
    """Test that fetch with valid data parses response."""
    async with AsyncZR_obj() as zr:
      team = ZRTeam()
      team.set_session(zr)
      # Mock response by directly setting _raw
      team._raw = {
        'name': 'Test Team',
        'riders': [
          {
            'riderId': 12345,
            'name': 'Rider 1',
            'gender': 'M',
            'height': 180.0,
            'weight': 75.0,
            'race': {
              'current': {
                'rating': 3.2,
                'mixed': {'category': 'A'},
                'womens': {'category': ''},
              },
              'max30': {
                'rating': 3.5,
                'mixed': {'category': 'A'},
                'womens': {'category': ''},
              },
              'max90': {
                'rating': 3.0,
                'mixed': {'category': 'B'},
                'womens': {'category': ''},
              },
            },
            'power': {
              'AWC': 10000.0,
              'CP': 280.0,
              'compoundScore': 2.5,
              'w5': 1500.0,
            },
          },
        ],
      }
      team.team_id = 456
      team._parse_response()
      assert team.team_name == 'Test Team'
      assert len(team.riders) == 1
      assert team.riders[0].zwift_id == 12345

  @pytest.mark.anyio
  async def test_fetch_handles_empty_riders(self):
    """Test fetch handles empty riders list."""
    async with AsyncZR_obj() as zr:
      team = ZRTeam()
      team.set_session(zr)
      team._raw = {
        'name': 'Test Team',
        'riders': [],
      }
      team.team_id = 456
      team._parse_response()
      assert team.team_name == 'Test Team'
      assert len(team.riders) == 0

  @pytest.mark.anyio
  async def test_fetch_handles_missing_nested_fields(self):
    """Test fetch handles missing nested fields in rider data."""
    async with AsyncZR_obj() as zr:
      team = ZRTeam()
      team.set_session(zr)
      team._raw = {
        'name': 'Test Team',
        'riders': [
          {
            'riderId': 12345,
            'name': 'Rider 1',
            # Missing race, power, and other fields
          },
        ],
      }
      team.team_id = 456
      team._parse_response()
      assert len(team.riders) == 1
      # Should have defaults for missing fields
      assert team.riders[0].current_rating == 0.0

  @pytest.mark.anyio
  async def test_fetch_with_mocked_session(self):
    """Test fetch with mocked session."""
    mock_zr = AsyncMock(spec=AsyncZR_obj)
    mock_zr.fetch_json = AsyncMock(
      return_value={
        'name': 'Mock Team',
        'riders': [
          {
            'riderId': 12345,
            'name': 'Mock Rider',
            'gender': 'M',
            'height': 175.0,
            'weight': 70.0,
            'race': {
              'current': {
                'rating': 3.5,
                'mixed': {'category': 'A'},
                'womens': {'category': ''},
              },
              'max30': {
                'rating': 3.8,
                'mixed': {'category': 'A'},
                'womens': {'category': ''},
              },
              'max90': {
                'rating': 3.2,
                'mixed': {'category': 'B'},
                'womens': {'category': ''},
              },
            },
            'power': {
              'AWC': 12000.0,
              'CP': 290.0,
              'compoundScore': 2.8,
            },
          },
        ],
      },
    )

    with patch('zrdatafetch.zrteam.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = 'test-token'
      mock_config_class.return_value = mock_config

      team = ZRTeam()
      team.set_session(mock_zr)
      team.team_id = 456

      await team.afetch()

      # Verify fetch_json was called with correct endpoint and headers
      mock_zr.fetch_json.assert_called_once()
      call_args = mock_zr.fetch_json.call_args
      assert '/public/clubs/456/0' in call_args[0]
      assert call_args[1]['headers']['Authorization'] == 'test-token'

      # Verify data was parsed
      assert team.team_name == 'Mock Team'
      assert len(team.riders) == 1
      assert team.riders[0].name == 'Mock Rider'

  @pytest.mark.anyio
  async def test_async_context_manager(self):
    """Test AsyncZRTeam works with async context manager."""
    async with AsyncZR_obj() as zr:
      team = ZRTeam()
      team.set_session(zr)
      assert team._zr is zr


# ===============================================================================
class TestAsyncZRTeamSession:
  """Test AsyncZRTeam session management."""

  @pytest.mark.anyio
  async def test_set_session(self):
    """Test set_session stores the ZR object."""
    async with AsyncZR_obj() as zr:
      team = ZRTeam()
      team.set_session(zr)
      assert team._zr is zr

  @pytest.mark.anyio
  async def test_multiple_teams_shared_session(self):
    """Test multiple teams can share same session."""
    async with AsyncZR_obj() as zr:
      team1 = ZRTeam()
      team2 = ZRTeam()
      team1.set_session(zr)
      team2.set_session(zr)
      assert team1._zr is team2._zr
      assert team1._zr is zr
