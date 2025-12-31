"""Live tests for Cyclist data fetching.

These tests make real API calls to zwiftpower.com and require valid credentials.
Run with: pytest -m live
"""

import pytest

from zpdatafetch.cyclist import Cyclist


@pytest.mark.live
def test_live_cyclist_fetch_single_id(valid_zwift_id):
  """Test fetching single Zwift ID via sync interface."""
  cyclist = Cyclist()
  result = cyclist.fetch(valid_zwift_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_zwift_id in result
  assert isinstance(result[valid_zwift_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(cyclist.raw, dict)
  assert valid_zwift_id in cyclist.raw
  assert isinstance(cyclist.raw[valid_zwift_id], str)

  # Validate processed attribute
  assert isinstance(cyclist.processed, dict)
  assert valid_zwift_id in cyclist.processed
  assert isinstance(cyclist.processed[valid_zwift_id], dict)

  # Validate data is non-empty
  assert len(cyclist.raw[valid_zwift_id]) > 0
  assert len(cyclist.processed[valid_zwift_id]) > 0


@pytest.mark.live
def test_live_cyclist_fetch_multiple_ids(valid_zwift_ids):
  """Test fetching multiple Zwift IDs via sync interface."""
  cyclist = Cyclist()
  result = cyclist.fetch(*valid_zwift_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_zwift_ids)

  # Validate all IDs are present
  for zwift_id in valid_zwift_ids:
    assert zwift_id in result
    assert isinstance(result[zwift_id], dict)

    # Validate raw data
    assert zwift_id in cyclist.raw
    assert isinstance(cyclist.raw[zwift_id], str)
    assert len(cyclist.raw[zwift_id]) > 0

    # Validate processed data
    assert zwift_id in cyclist.processed
    assert isinstance(cyclist.processed[zwift_id], dict)
    assert len(cyclist.processed[zwift_id]) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_cyclist_afetch_single_id(valid_zwift_id):
  """Test fetching single Zwift ID via async interface."""
  cyclist = Cyclist()
  result = await cyclist.afetch(valid_zwift_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_zwift_id in result
  assert isinstance(result[valid_zwift_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(cyclist.raw, dict)
  assert valid_zwift_id in cyclist.raw
  assert isinstance(cyclist.raw[valid_zwift_id], str)

  # Validate processed attribute
  assert isinstance(cyclist.processed, dict)
  assert valid_zwift_id in cyclist.processed
  assert isinstance(cyclist.processed[valid_zwift_id], dict)

  # Validate data is non-empty
  assert len(cyclist.raw[valid_zwift_id]) > 0
  assert len(cyclist.processed[valid_zwift_id]) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_cyclist_afetch_multiple_ids(valid_zwift_ids):
  """Test fetching multiple Zwift IDs via async interface."""
  cyclist = Cyclist()
  result = await cyclist.afetch(*valid_zwift_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_zwift_ids)

  # Validate all IDs are present
  for zwift_id in valid_zwift_ids:
    assert zwift_id in result
    assert isinstance(result[zwift_id], dict)

    # Validate raw data
    assert zwift_id in cyclist.raw
    assert isinstance(cyclist.raw[zwift_id], str)
    assert len(cyclist.raw[zwift_id]) > 0

    # Validate processed data
    assert zwift_id in cyclist.processed
    assert isinstance(cyclist.processed[zwift_id], dict)
    assert len(cyclist.processed[zwift_id]) > 0
