"""Live tests for Result data fetching.

These tests make real API calls to zwiftpower.com and require valid credentials.
Run with: pytest -m live
"""

import pytest

from zpdatafetch.result import Result
from zpdatafetch.zpraceresult import ZPRaceResult


@pytest.mark.live
def test_live_result_fetch_single_id(valid_event_id):
  """Test fetching single event ID via sync interface."""
  result_obj = Result()
  result = result_obj.fetch(valid_event_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], ZPRaceResult)

  # Validate raw attribute contains string data
  assert isinstance(result_obj.raw(), dict)
  assert valid_event_id in result_obj.raw()
  assert isinstance(result_obj.raw()[valid_event_id], str)

  # Validate fetched attribute
  assert isinstance(result_obj._fetched, dict)
  assert valid_event_id in result_obj._fetched
  assert isinstance(result_obj._fetched[valid_event_id], ZPRaceResult)

  # Validate data is non-empty
  assert len(result_obj.raw()[valid_event_id]) > 0
  assert len(result_obj._fetched[valid_event_id]) > 0


@pytest.mark.live
def test_live_result_fetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via sync interface."""
  result_obj = Result()
  result = result_obj.fetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], ZPRaceResult)

    # Validate raw data
    assert event_id in result_obj.raw()
    assert isinstance(result_obj.raw()[event_id], str)
    assert len(result_obj.raw()[event_id]) > 0

    # Validate fetched data
    assert event_id in result_obj._fetched
    assert isinstance(result_obj._fetched[event_id], ZPRaceResult)
    assert len(result_obj._fetched[event_id]) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_result_afetch_single_id(valid_event_id):
  """Test fetching single event ID via async interface."""
  result_obj = Result()
  result = await result_obj.afetch(valid_event_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], ZPRaceResult)

  # Validate raw attribute contains string data
  assert isinstance(result_obj.raw(), dict)
  assert valid_event_id in result_obj.raw()
  assert isinstance(result_obj.raw()[valid_event_id], str)

  # Validate fetched attribute
  assert isinstance(result_obj._fetched, dict)
  assert valid_event_id in result_obj._fetched
  assert isinstance(result_obj._fetched[valid_event_id], ZPRaceResult)

  # Validate data is non-empty
  assert len(result_obj.raw()[valid_event_id]) > 0
  assert len(result_obj._fetched[valid_event_id]) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_result_afetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via async interface."""
  result_obj = Result()
  result = await result_obj.afetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], ZPRaceResult)

    # Validate raw data
    assert event_id in result_obj.raw()
    assert isinstance(result_obj.raw()[event_id], str)
    assert len(result_obj.raw()[event_id]) > 0

    # Validate fetched data
    assert event_id in result_obj._fetched
    assert isinstance(result_obj._fetched[event_id], ZPRaceResult)
    assert len(result_obj._fetched[event_id]) > 0
