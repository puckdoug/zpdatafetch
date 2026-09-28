"""Live tests for ZwiftRideOns against the real Zwift API (gh#11)."""

import pytest

from zdatafetch.activity import ZwiftActivity
from zdatafetch.rideons import ZwiftRideOns


def _rideons_with_data(rider_id):
  """Fetch RideOns for recent activities until one is non-empty."""
  acts = ZwiftActivity()
  acts.fetch(rider_id, start=0, limit=20)
  for activity_id in acts.activity_ids()[:5]:
    rideons = ZwiftRideOns()
    rideons.fetch(rider_id, activity_id)
    if rideons.rideon_count() > 0:
      return rideons
  pytest.skip('no RideOns found in recent activities')


@pytest.mark.live
def test_live_rideons_record_shape(zdata_rider_id):
  """Production records must nest the rider ID at profile.id (gh#11)."""
  rideons = _rideons_with_data(zdata_rider_id)
  for record in rideons.rideons:
    profile = record.get('profile')
    assert isinstance(profile, dict)
    assert isinstance(profile.get('id'), int)
    assert profile['id'] == record['profileId']
    assert isinstance(record['id'], int)


@pytest.mark.live
def test_live_rideon_ids_are_rider_ids(zdata_rider_id):
  """rideon_ids() must return rider IDs that has_rideon_from() matches."""
  rideons = _rideons_with_data(zdata_rider_id)
  ids = rideons.rideon_ids()
  assert len(ids) > 0
  assert all(isinstance(i, int) for i in ids)
  for record in rideons.rideons:
    profile = record.get('profile')
    if isinstance(profile, dict) and isinstance(profile.get('id'), int):
      assert rideons.has_rideon_from(profile['id']) is True
  assert rideons.has_rideon_from(0) is False
