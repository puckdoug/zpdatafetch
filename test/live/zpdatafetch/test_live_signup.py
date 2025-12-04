"""Live tests for Signup data fetching.

These tests make real API calls to zwiftpower.com and require valid credentials.
Run with: pytest --live
"""

import pytest

from zpdatafetch.signup import Signup


@pytest.mark.live
def test_live_signup_fetch_single_id(valid_event_id):
  """Test fetching single event ID via sync interface."""
  signup = Signup()
  result = signup.fetch(valid_event_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(signup.raw, dict)
  assert valid_event_id in signup.raw
  assert isinstance(signup.raw[valid_event_id], str)

  # Validate processed attribute
  assert isinstance(signup.processed, dict)
  assert valid_event_id in signup.processed
  assert isinstance(signup.processed[valid_event_id], dict)

  # Validate data is non-empty
  assert len(signup.raw[valid_event_id]) > 0


@pytest.mark.live
def test_live_signup_fetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via sync interface."""
  signup = Signup()
  result = signup.fetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], dict)

    # Validate raw data
    assert event_id in signup.raw
    assert isinstance(signup.raw[event_id], str)
    assert len(signup.raw[event_id]) > 0

    # Validate processed data
    assert event_id in signup.processed
    assert isinstance(signup.processed[event_id], dict)


@pytest.mark.live
@pytest.mark.anyio
async def test_live_signup_afetch_single_id(valid_event_id):
  """Test fetching single event ID via async interface."""
  signup = Signup()
  result = await signup.afetch(valid_event_id)

  # Validate response structure
  assert isinstance(result, dict)
  assert valid_event_id in result
  assert isinstance(result[valid_event_id], dict)

  # Validate raw attribute contains string data
  assert isinstance(signup.raw, dict)
  assert valid_event_id in signup.raw
  assert isinstance(signup.raw[valid_event_id], str)

  # Validate processed attribute
  assert isinstance(signup.processed, dict)
  assert valid_event_id in signup.processed
  assert isinstance(signup.processed[valid_event_id], dict)

  # Validate data is non-empty
  assert len(signup.raw[valid_event_id]) > 0


@pytest.mark.live
@pytest.mark.anyio
async def test_live_signup_afetch_multiple_ids(valid_event_ids):
  """Test fetching multiple event IDs via async interface."""
  signup = Signup()
  result = await signup.afetch(*valid_event_ids)

  # Validate response structure
  assert isinstance(result, dict)
  assert len(result) == len(valid_event_ids)

  # Validate all IDs are present
  for event_id in valid_event_ids:
    assert event_id in result
    assert isinstance(result[event_id], dict)

    # Validate raw data
    assert event_id in signup.raw
    assert isinstance(signup.raw[event_id], str)
    assert len(signup.raw[event_id]) > 0

    # Validate processed data
    assert event_id in signup.processed
    assert isinstance(signup.processed[event_id], dict)
