"""Live tests for Primes data fetching.

These tests make real API calls to zwiftpower.com and require valid credentials.
Run with: pytest -m live
"""

import pytest

from zpdatafetch.primes import Primes


@pytest.mark.live
def test_live_primes_fetch_single_id(valid_event_id):
  """Test fetching single event ID via sync interface."""
  primes = Primes()
  result = primes.fetch(valid_event_id)

  # Validate response structure - Primes has nested dict structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], dict)

  # Validate raw attribute has nested structure: {race_id: {cat: {type: str}}}
  assert isinstance(primes.raw, dict)
  assert valid_event_id in primes.raw
  assert isinstance(primes.raw[valid_event_id], dict)

  # Check at least one category exists
  assert len(primes.raw[valid_event_id]) > 0

  # Validate one category/type has string data
  first_cat = list(primes.raw[valid_event_id].keys())[0]
  assert isinstance(primes.raw[valid_event_id][first_cat], dict)
  first_type = list(primes.raw[valid_event_id][first_cat].keys())[0]
  assert isinstance(primes.raw[valid_event_id][first_cat][first_type], str)

  # Validate processed attribute
  assert isinstance(primes.processed, dict)
  assert valid_event_id in primes.processed
  assert isinstance(primes.processed[valid_event_id], dict)


@pytest.mark.live
def test_live_primes_fetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via sync interface."""
  primes = Primes()
  result = primes.fetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], dict)

    # Validate raw data has nested structure
    assert event_id in primes.raw
    assert isinstance(primes.raw[event_id], dict)
    assert len(primes.raw[event_id]) > 0

    # Validate processed data
    assert event_id in primes.processed
    assert isinstance(primes.processed[event_id], dict)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_primes_afetch_single_id(valid_event_id):
  """Test fetching single event ID via async interface."""
  primes = Primes()
  result = await primes.afetch(valid_event_id)

  # Validate response structure - Primes has nested dict structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], dict)

  # Validate raw attribute has nested structure: {race_id: {cat: {type: str}}}
  assert isinstance(primes.raw, dict)
  assert valid_event_id in primes.raw
  assert isinstance(primes.raw[valid_event_id], dict)

  # Check at least one category exists
  assert len(primes.raw[valid_event_id]) > 0

  # Validate one category/type has string data
  first_cat = list(primes.raw[valid_event_id].keys())[0]
  assert isinstance(primes.raw[valid_event_id][first_cat], dict)
  first_type = list(primes.raw[valid_event_id][first_cat].keys())[0]
  assert isinstance(primes.raw[valid_event_id][first_cat][first_type], str)

  # Validate processed attribute
  assert isinstance(primes.processed, dict)
  assert valid_event_id in primes.processed
  assert isinstance(primes.processed[valid_event_id], dict)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_primes_afetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via async interface."""
  primes = Primes()
  result = await primes.afetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], dict)

    # Validate raw data has nested structure
    assert event_id in primes.raw
    assert isinstance(primes.raw[event_id], dict)
    assert len(primes.raw[event_id]) > 0

    # Validate processed data
    assert event_id in primes.processed
    assert isinstance(primes.processed[event_id], dict)
