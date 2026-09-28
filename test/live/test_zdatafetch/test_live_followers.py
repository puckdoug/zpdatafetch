"""Live tests for ZwiftFollowers pagination against the real API (gh#8)."""

import pytest

from zdatafetch.followers import ZwiftFollowers

# Set to a rider ID known to have >200 followers to bypass the probe.
MANY_FOLLOWERS_RIDER = None


def _rider_with_many_followers(rider_id):
  """Find a rider with >200 followers, probing locally first."""
  if MANY_FOLLOWERS_RIDER is not None:
    return MANY_FOLLOWERS_RIDER
  obj = ZwiftFollowers()
  obj.fetch(rider_id)
  if obj.follower_count() > 200:
    return rider_id
  for record in obj.followers:
    profile = record.get('followerProfile') or {}
    social = profile.get('socialFacts') or {}
    if (social.get('followersCount') or 0) > 200:
      return profile['id']
  pytest.skip('no rider with >200 followers reachable from fixture rider')


@pytest.mark.live
def test_live_followers_record_shape(zdata_rider_id):
  """Page-1 follower records carry the documented relation shape (gh#8)."""
  obj = ZwiftFollowers()
  obj.fetch(zdata_rider_id)
  assert obj.follower_count() > 0
  for record in obj.followers:
    assert isinstance(record.get('id'), int)
    assert isinstance(record.get('followerId'), int)
    assert isinstance(record.get('followeeId'), int)
  well_formed = [
    r for r in obj.followers
    if isinstance(r.get('followerProfile'), dict)
  ]
  assert well_formed, 'no follower records with a profile object'
  for record in well_formed:
    assert isinstance(record['followerProfile'].get('id'), int)


@pytest.mark.live
def test_live_followees_record_shape(zdata_rider_id):
  """Followee records mirror the relation shape (gh#8)."""
  obj = ZwiftFollowers()
  obj.fetch(zdata_rider_id, include_followers=False)
  for record in obj.followees:
    assert isinstance(record.get('id'), int)


@pytest.mark.live
def test_live_followers_pagination(zdata_rider_id):
  """A rider with >200 followers gets the complete list (gh#8)."""
  target = _rider_with_many_followers(zdata_rider_id)
  obj = ZwiftFollowers()
  obj.fetch(target)
  assert obj.follower_count() > 200
  assert len(obj.followers) == obj.follower_count()


@pytest.mark.live
def test_live_followees_fetch(zdata_rider_id):
  """Followees fetch cleanly through the paginated helper (gh#8)."""
  obj = ZwiftFollowers()
  obj.fetch(zdata_rider_id, include_followers=False)
  assert obj.followee_count() == len(obj.followees)
