"""Live tests for ZRResultFetch that make real API calls to zwiftracing.app."""

import pytest

from zrdatafetch import ZRResultFetch


@pytest.mark.live
def test_live_zrresult_fetch_single_id(valid_event_id):
  """Test synchronous fetch of a single result ID."""
  fetcher = ZRResultFetch()
  results = fetcher.fetch(valid_event_id)

  assert valid_event_id in results
  result = results[valid_event_id]

  # Verify parsed data
  assert result.race_id == valid_event_id
  assert len(result) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrresult_afetch_single_id(valid_event_id):
  """Test asynchronous fetch of a single result ID."""
  fetcher = ZRResultFetch()
  results = await fetcher.afetch(valid_event_id)

  assert valid_event_id in results
  result = results[valid_event_id]

  # Verify parsed data
  assert result.race_id == valid_event_id
  assert len(result) > 0
