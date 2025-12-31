"""Fixtures for zrdatafetch live tests."""

import pytest


@pytest.fixture
def valid_zwift_id():
  """Single valid Zwift ID for rider tests."""
  return 486314


@pytest.fixture
def valid_zwift_ids():
  """Multiple valid Zwift IDs for rider tests."""
  return [486314, 2417653]


@pytest.fixture
def valid_event_id():
  """Single valid event ID for result tests."""
  return 5240126


@pytest.fixture
def valid_event_ids():
  """Multiple valid event IDs for result tests."""
  return [5240126, 5240100]


@pytest.fixture
def valid_team_id():
  """Single valid team ID for team tests."""
  return 21663
