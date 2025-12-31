"""Fixtures for live zpdatafetch tests.

These fixtures provide known valid IDs for testing live API calls.
"""

import json

import pytest


@pytest.fixture
def valid_zwift_id():
  """Single valid Zwift ID for testing."""
  return 486314


@pytest.fixture
def valid_zwift_ids():
  """Multiple valid Zwift IDs for testing."""
  return [486314, 2417653]


@pytest.fixture
def valid_event_id():
  """Single valid event ID for testing."""
  return 5240126


@pytest.fixture
def valid_event_ids():
  """Multiple valid event IDs for testing."""
  return [5240126, 5240100]


@pytest.fixture
def valid_team_id():
  """Single valid team ID for testing."""
  return 21663


@pytest.fixture
def valid_league_id():
  """Single valid league ID for testing."""
  return 1990


@pytest.fixture
def valid_league_ids():
  """Multiple valid league IDs for testing."""
  return [1990, 2678, 3017]


@pytest.fixture
def league_fixtures():
  """Load league fixture data from tmp/ directory.

  The fixture files contain the processed format: {"id": {data}}
  We extract the data dict for each ID.
  """
  fixtures = {}
  for league_id in [1990, 2678, 3017]:
    with open(f'tmp/league_{league_id}.json', encoding='utf8') as f:
      data = json.load(f)
      # data is {"1990": {...}} - extract the value for the string key
      fixtures[league_id] = data[str(league_id)]
  return fixtures
