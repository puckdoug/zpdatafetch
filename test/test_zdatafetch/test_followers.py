"""Tests for Zwift followers/followees data fetching (stub)."""

import pytest

from zdatafetch.followers import ZwiftFollowers


def test_followers_initialization(mock_auth):
  """Test ZwiftFollowers initialization."""
  followers = ZwiftFollowers(mock_auth)

  assert followers.auth == mock_auth
  assert followers._raw == {}
  assert followers._fetched == {}


def test_fetch_not_implemented(mock_followers):
  """Test that fetch raises NotImplementedError."""
  with pytest.raises(
    NotImplementedError,
    match='Follower fetching is not yet implemented',
  ):
    mock_followers.fetch(550564)


def test_fetch_multiple_not_implemented(mock_followers):
  """Test that fetch with multiple IDs raises NotImplementedError."""
  with pytest.raises(
    NotImplementedError,
    match='Follower fetching is not yet implemented',
  ):
    mock_followers.fetch(550564, 123456, 789012)
