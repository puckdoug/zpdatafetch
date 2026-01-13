"""Tests for Zwift RideOn data fetching (stub)."""

import pytest

from zdatafetch.rideons import ZwiftRideOns


def test_rideons_initialization(mock_auth):
  """Test ZwiftRideOns initialization."""
  rideons = ZwiftRideOns(mock_auth)

  assert rideons.auth == mock_auth
  assert rideons._raw == {}
  assert rideons._fetched == {}


def test_fetch_not_implemented(mock_rideons):
  """Test that fetch raises NotImplementedError."""
  with pytest.raises(
    NotImplementedError,
    match='RideOn fetching is not yet implemented',
  ):
    mock_rideons.fetch(12345)


def test_fetch_multiple_not_implemented(mock_rideons):
  """Test that fetch with multiple IDs raises NotImplementedError."""
  with pytest.raises(
    NotImplementedError,
    match='RideOn fetching is not yet implemented',
  ):
    mock_rideons.fetch(12345, 67890, 11111)
