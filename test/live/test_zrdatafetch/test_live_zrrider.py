"""Live tests for ZRRiderFetch that make real API calls to zwiftracing.app."""

import pytest

from zrdatafetch import ZRRiderFetch


@pytest.mark.live
def test_live_zrrider_fetch_single_id(valid_zwift_id):
  """Test synchronous fetch of a single rider ID."""
  fetcher = ZRRiderFetch()
  riders = fetcher.fetch(valid_zwift_id)

  assert valid_zwift_id in riders
  rider = riders[valid_zwift_id]

  # Verify parsed data
  assert rider.zwift_id == valid_zwift_id
  assert rider.name is not None
  assert isinstance(rider.name, str)


@pytest.mark.live
def test_live_zrrider_fetch_multiple_ids(valid_zwift_ids):
  """Test synchronous fetch of multiple rider IDs."""
  riders = ZRRiderFetch.fetch_batch(*valid_zwift_ids)

  # Verify we got results (may not be all IDs due to API limits)
  assert len(riders) > 0
  assert isinstance(riders, dict)

  # Verify each returned rider
  for zwift_id, rider in riders.items():
    assert isinstance(zwift_id, int)
    assert rider.name is not None
    assert isinstance(rider.name, str)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrrider_afetch_single_id(valid_zwift_id):
  """Test asynchronous fetch of a single rider ID."""
  fetcher = ZRRiderFetch()
  riders = await fetcher.afetch(valid_zwift_id)

  assert valid_zwift_id in riders
  rider = riders[valid_zwift_id]

  # Verify parsed data
  assert rider.zwift_id == valid_zwift_id
  assert rider.name is not None
  assert isinstance(rider.name, str)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrrider_afetch_multiple_ids(valid_zwift_ids):
  """Test asynchronous fetch of multiple rider IDs."""
  riders = await ZRRiderFetch.afetch_batch(*valid_zwift_ids)

  # Verify we got results (may not be all IDs due to API limits)
  assert len(riders) > 0
  assert isinstance(riders, dict)

  # Verify each returned rider
  for zwift_id, rider in riders.items():
    assert isinstance(zwift_id, int)
    assert rider.name is not None
    assert isinstance(rider.name, str)
