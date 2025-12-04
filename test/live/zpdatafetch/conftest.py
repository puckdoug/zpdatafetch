"""Fixtures for live zpdatafetch tests.

These fixtures provide known valid IDs for testing live API calls.
"""

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
