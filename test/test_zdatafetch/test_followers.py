"""Tests for Zwift followers/followees data fetching."""

import json

from zdatafetch.followers import ZwiftFollowers


def test_followers_initialization():
  """Test ZwiftFollowers initialization."""
  followers = ZwiftFollowers()

  assert followers._raw == ''
  assert followers._fetched == {}
  assert followers.rider_id == 0
  assert followers.followers == []
  assert followers.followees == []


def test_parse_response():
  """Test parsing raw follower data."""
  followers = ZwiftFollowers()
  followers.rider_id = 550564

  raw_data = {
    'followers': json.dumps(
      [
        {'id': 123456, 'firstName': 'John', 'lastName': 'Doe'},
        {'id': 789012, 'firstName': 'Jane', 'lastName': 'Smith'},
      ],
    ),
    'followees': json.dumps(
      [
        {'id': 111222, 'firstName': 'Bob', 'lastName': 'Jones'},
      ],
    ),
  }

  followers._parse_response(raw_data)

  assert len(followers.followers) == 2
  assert len(followers.followees) == 1
  assert followers.followers[0]['id'] == 123456
  assert followers.followees[0]['id'] == 111222


def test_follower_count():
  """Test follower count helper."""
  followers = ZwiftFollowers()
  followers.followers = [
    {'id': 1},
    {'id': 2},
    {'id': 3},
  ]

  assert followers.follower_count() == 3


def test_followee_count():
  """Test followee count helper."""
  followers = ZwiftFollowers()
  followers.followees = [
    {'id': 1},
    {'id': 2},
  ]

  assert followers.followee_count() == 2


def test_follower_ids():
  """Test extracting follower IDs."""
  followers = ZwiftFollowers()
  followers.followers = [
    {'id': 123, 'firstName': 'John'},
    {'id': 456, 'firstName': 'Jane'},
  ]

  ids = followers.follower_ids()
  assert ids == [123, 456]


def test_followee_ids():
  """Test extracting followee IDs."""
  followers = ZwiftFollowers()
  followers.followees = [
    {'id': 789, 'firstName': 'Bob'},
    {'id': 101, 'firstName': 'Alice'},
  ]

  ids = followers.followee_ids()
  assert ids == [789, 101]


def test_mutual_followers():
  """Test finding mutual followers."""
  followers = ZwiftFollowers()
  followers.followers = [
    {'id': 123, 'firstName': 'John'},
    {'id': 456, 'firstName': 'Jane'},
    {'id': 789, 'firstName': 'Bob'},
  ]
  followers.followees = [
    {'id': 123, 'firstName': 'John'},  # Mutual
    {'id': 999, 'firstName': 'Alice'},
  ]

  mutual = followers.mutual_followers()
  assert len(mutual) == 1
  assert mutual[0]['id'] == 123


def test_str_representation():
  """Test string representation."""
  followers = ZwiftFollowers()
  followers.rider_id = 550564
  followers.followers = [{'id': 1}, {'id': 2}]
  followers.followees = [{'id': 3}]
  followers._fetched = {
    'followers': followers.followers,
    'followees': followers.followees,
  }

  output = str(followers)
  assert 'ZwiftFollowers(rider_id=550564)' in output
  assert 'followers:' in output
  assert 'followees:' in output


def test_json_serialization():
  """Test JSON serialization."""
  followers = ZwiftFollowers()
  followers._fetched = {
    'followers': [{'id': 123}],
    'followees': [{'id': 456}],
  }

  json_str = followers.json()
  data = json.loads(json_str)
  assert 'followers' in data
  assert 'followees' in data
  assert len(data['followers']) == 1
  assert len(data['followees']) == 1


def test_asdict():
  """Test dictionary access."""
  followers = ZwiftFollowers()
  followers._fetched = {'followers': [], 'followees': []}

  data = followers.asdict()
  assert isinstance(data, dict)
  assert 'followers' in data
  assert 'followees' in data
