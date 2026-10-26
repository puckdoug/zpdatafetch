"""Live tests for ZRResultFetch that make real API calls to zwiftracing.app."""

import time

import pytest

from zrdatafetch import ZRResultFetch

_RESULT_REQUEST_INTERVAL = 60.0
_last_result_request = 0.0


@pytest.fixture(autouse=True)
def space_live_result_requests():
  """Wait between live result requests.

  The standard Zwiftracing tier allows one /public/results request per
  minute. Each live test makes a fresh request, so space them out rather
  than caching data between tests.
  """
  global _last_result_request

  if _last_result_request:
    wait = _RESULT_REQUEST_INTERVAL - (
      time.monotonic() - _last_result_request
    )
    if wait > 0:
      time.sleep(wait)

  yield

  _last_result_request = time.monotonic()


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
