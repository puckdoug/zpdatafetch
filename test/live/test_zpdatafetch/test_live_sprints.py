"""Live tests for Sprints data fetching.

These tests make real API calls to zwiftpower.com and require valid credentials.
Run with: pytest -m live
"""

import pytest

from zpdatafetch.sprints import Sprints


@pytest.mark.live
def test_live_sprints_fetch_single_id(valid_event_id):
  """Test fetching single event ID via sync interface."""
  sprints = Sprints()
  result = sprints.fetch(valid_event_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(sprints.raw, dict)
  assert valid_event_id in sprints.raw
  assert isinstance(sprints.raw[valid_event_id], str)

  # Validate processed attribute
  assert isinstance(sprints.processed, dict)
  assert valid_event_id in sprints.processed
  assert isinstance(sprints.processed[valid_event_id], dict)

  # Validate data is non-empty
  assert len(sprints.raw[valid_event_id]) > 0


@pytest.mark.live
def test_live_sprints_fetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via sync interface."""
  sprints = Sprints()
  result = sprints.fetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], dict)

    # Validate raw data
    assert event_id in sprints.raw
    assert isinstance(sprints.raw[event_id], str)
    assert len(sprints.raw[event_id]) > 0

    # Validate processed data
    assert event_id in sprints.processed
    assert isinstance(sprints.processed[event_id], dict)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_sprints_afetch_single_id(valid_event_id):
  """Test fetching single event ID via async interface."""
  sprints = Sprints()
  result = await sprints.afetch(valid_event_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(sprints.raw, dict)
  assert valid_event_id in sprints.raw
  assert isinstance(sprints.raw[valid_event_id], str)

  # Validate processed attribute
  assert isinstance(sprints.processed, dict)
  assert valid_event_id in sprints.processed
  assert isinstance(sprints.processed[valid_event_id], dict)

  # Validate data is non-empty
  assert len(sprints.raw[valid_event_id]) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_sprints_afetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via async interface."""
  sprints = Sprints()
  result = await sprints.afetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], dict)

    # Validate raw data
    assert event_id in sprints.raw
    assert isinstance(sprints.raw[event_id], str)
    assert len(sprints.raw[event_id]) > 0

    # Validate processed data
    assert event_id in sprints.processed
    assert isinstance(sprints.processed[event_id], dict)
