"""Live tests for League data fetching.

These tests make real API calls to zwiftpower.com and require valid credentials.
Run with: pytest --live
"""

import pytest

from zpdatafetch.league import League


@pytest.mark.live
def test_live_league_fetch_single_id(valid_league_id, league_fixtures):
  """Test fetching single league ID via sync interface."""
  league = League()
  result = league.fetch(valid_league_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_league_id in result
  assert isinstance(result[valid_league_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(league.raw, dict)
  assert valid_league_id in league.raw
  assert isinstance(league.raw[valid_league_id], str)

  # Validate processed attribute
  assert isinstance(league.processed, dict)
  assert valid_league_id in league.processed
  assert isinstance(league.processed[valid_league_id], dict)

  # Validate data is non-empty
  assert len(league.raw[valid_league_id]) > 0
  assert len(league.processed[valid_league_id]) > 0

  # Compare against fixture
  assert result[valid_league_id] == league_fixtures[valid_league_id]


@pytest.mark.live
def test_live_league_fetch_multiple_ids(valid_league_ids, league_fixtures):
  """Test fetching multiple league IDs via sync interface."""
  league = League()
  result = league.fetch(*valid_league_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_league_ids)

  # Validate all IDs are present
  for league_id in valid_league_ids:
    assert league_id in result
    assert isinstance(result[league_id], dict)

    # Validate raw data
    assert league_id in league.raw
    assert isinstance(league.raw[league_id], str)
    assert len(league.raw[league_id]) > 0

    # Validate processed data
    assert league_id in league.processed
    assert isinstance(league.processed[league_id], dict)
    assert len(league.processed[league_id]) > 0

    # Compare against fixture
    assert result[league_id] == league_fixtures[league_id]


@pytest.mark.live
@pytest.mark.anyio
async def test_live_league_afetch_single_id(valid_league_id, league_fixtures):
  """Test fetching single league ID via async interface."""
  league = League()
  result = await league.afetch(valid_league_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_league_id in result
  assert isinstance(result[valid_league_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(league.raw, dict)
  assert valid_league_id in league.raw
  assert isinstance(league.raw[valid_league_id], str)

  # Validate processed attribute
  assert isinstance(league.processed, dict)
  assert valid_league_id in league.processed
  assert isinstance(league.processed[valid_league_id], dict)

  # Validate data is non-empty
  assert len(league.raw[valid_league_id]) > 0
  assert len(league.processed[valid_league_id]) > 0

  # Compare against fixture
  assert result[valid_league_id] == league_fixtures[valid_league_id]


@pytest.mark.live
@pytest.mark.anyio
async def test_live_league_afetch_multiple_ids(valid_league_ids, league_fixtures):
  """Test fetching multiple league IDs via async interface."""
  league = League()
  result = await league.afetch(*valid_league_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_league_ids)

  # Validate all IDs are present
  for league_id in valid_league_ids:
    assert league_id in result
    assert isinstance(result[league_id], dict)

    # Validate raw data
    assert league_id in league.raw
    assert isinstance(league.raw[league_id], str)
    assert len(league.raw[league_id]) > 0

    # Validate processed data
    assert league_id in league.processed
    assert isinstance(league.processed[league_id], dict)
    assert len(league.processed[league_id]) > 0

    # Compare against fixture
    assert result[league_id] == league_fixtures[league_id]
