"""Live tests for ZRRider that make real API calls to zwiftracing.app."""

import pytest

from zrdatafetch.zrrider import ZRRider


@pytest.mark.live
def test_live_zrrider_fetch_single_id(valid_zwift_id):
  """Test synchronous fetch of a single rider ID."""
  rider = ZRRider(zwift_id=valid_zwift_id)
  rider.fetch()

  # Verify raw data exists and is a string
  assert rider._raw is not None
  assert isinstance(rider._raw, str)
  assert len(rider._raw) > 0

  # Verify parsed data
  assert rider.zwift_id == valid_zwift_id
  assert rider.name is not None
  assert isinstance(rider.name, str)


@pytest.mark.live
def test_live_zrrider_fetch_multiple_ids(valid_zwift_ids):
  """Test synchronous fetch of multiple rider IDs."""
  riders = ZRRider.fetch_batch(*valid_zwift_ids)

  # Verify we got results (may not be all IDs due to API limits)
  assert len(riders) > 0
  assert isinstance(riders, dict)

  # Verify each returned rider
  for zwift_id, rider in riders.items():
    assert isinstance(zwift_id, int)
    assert isinstance(rider, ZRRider)
    assert rider.name is not None
    assert isinstance(rider.name, str)
    assert rider._raw is not None
    assert isinstance(rider._raw, str)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrrider_afetch_single_id(valid_zwift_id):
  """Test asynchronous fetch of a single rider ID."""
  rider = ZRRider(zwift_id=valid_zwift_id)
  await rider.afetch()

  # Verify raw data exists and is a string
  assert rider._raw is not None
  assert isinstance(rider._raw, str)
  assert len(rider._raw) > 0

  # Verify parsed data
  assert rider.zwift_id == valid_zwift_id
  assert rider.name is not None
  assert isinstance(rider.name, str)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrrider_afetch_multiple_ids(valid_zwift_ids):
  """Test asynchronous fetch of multiple rider IDs."""
  riders = await ZRRider.afetch_batch(*valid_zwift_ids)

  # Verify we got results (may not be all IDs due to API limits)
  assert len(riders) > 0
  assert isinstance(riders, dict)

  # Verify each returned rider
  for zwift_id, rider in riders.items():
    assert isinstance(zwift_id, int)
    assert isinstance(rider, ZRRider)
    assert rider.name is not None
    assert isinstance(rider.name, str)
    assert rider._raw is not None
    assert isinstance(rider._raw, str)
