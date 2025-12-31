"""Live tests for ZRResult that make real API calls to zwiftracing.app."""

import pytest

from zrdatafetch.zrresult import ZRResult


@pytest.mark.live
def test_live_zrresult_fetch_single_id(valid_event_id):
  """Test synchronous fetch of a single result ID."""
  result = ZRResult(race_id=valid_event_id)
  result.fetch()

  # Verify raw data exists and is a string
  assert result._raw is not None
  assert isinstance(result._raw, str)
  assert len(result._raw) > 0

  # Verify parsed data
  assert result.race_id == valid_event_id
  assert result.results is not None
  assert isinstance(result.results, list)
  assert len(result.results) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrresult_afetch_single_id(valid_event_id):
  """Test asynchronous fetch of a single result ID."""
  result = ZRResult(race_id=valid_event_id)
  await result.afetch()

  # Verify raw data exists and is a string
  assert result._raw is not None
  assert isinstance(result._raw, str)
  assert len(result._raw) > 0

  # Verify parsed data
  assert result.race_id == valid_event_id
  assert result.results is not None
  assert isinstance(result.results, list)
  assert len(result.results) > 0
