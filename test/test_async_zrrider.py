"""Tests for ZRRider class with async (afetch) methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.zrrider import ZRRider


# ===============================================================================
class TestAsyncZRRiderFetch:
  """Test AsyncZRRider.fetch() method."""

  @pytest.mark.anyio
  async def test_fetch_no_zwift_id(self):
    """Test fetch with no zwift_id returns silently."""
    async with AsyncZR_obj() as zr:
      rider = ZRRider()
      rider.set_session(zr)
      # Should return without error when zwift_id is 0
      await rider.afetch()
      assert rider.zwift_id == 0

  @pytest.mark.anyio
  async def test_fetch_sets_attributes(self):
    """Test that fetch with valid data sets attributes."""
    async with AsyncZR_obj() as zr:
      rider = ZRRider()
      rider.set_session(zr)
      # Mock response by directly setting _raw
      rider._raw = {
        'name': 'Test Rider',
        'gender': 'M',
        'power': {'compoundScore': 2.5},
        'race': {
          'current': {'rating': 3.2, 'mixed': {'category': 'A'}},
          'max30': {'rating': 3.5, 'mixed': {'category': 'A'}},
          'max90': {'rating': 3.0, 'mixed': {'category': 'B'}},
        },
      }
      rider.zwift_id = 12345
      rider._parse_response()
      assert rider.name == 'Test Rider'
      assert rider.current_rating == 3.2

  @pytest.mark.anyio
  async def test_async_context_manager(self):
    """Test AsyncZRRider works with async context manager."""
    async with AsyncZR_obj() as zr:
      rider = ZRRider()
      rider.set_session(zr)
      assert rider._zr is zr

  @pytest.mark.anyio
  async def test_fetch_with_mocked_session(self):
    """Test fetch calls the session with correct endpoint."""
    mock_zr = AsyncMock(spec=AsyncZR_obj)
    mock_zr.fetch_json = AsyncMock(
      return_value={
        'name': 'Mock Rider',
        'gender': 'F',
        'power': {'compoundScore': 3.0},
        'race': {
          'current': {'rating': 4.0, 'mixed': {'category': 'A'}},
          'max30': {'rating': 4.5, 'mixed': {'category': 'A'}},
          'max90': {'rating': 3.8, 'mixed': {'category': 'A'}},
        },
      },
    )

    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = 'test-token'
      mock_config_class.return_value = mock_config

      rider = ZRRider()
      rider.set_session(mock_zr)
      rider.zwift_id = 12345

      await rider.afetch()

      # Verify fetch_json was called with correct endpoint and headers
      mock_zr.fetch_json.assert_called_once()
      call_args = mock_zr.fetch_json.call_args
      assert '/public/riders/12345' in call_args[0]
      assert call_args[1]['headers']['Authorization'] == 'test-token'

      # Verify data was parsed
      assert rider.name == 'Mock Rider'
      assert rider.current_rating == 4.0

  @pytest.mark.anyio
  async def test_fetch_with_epoch(self):
    """Test fetch includes epoch in endpoint when provided."""
    mock_zr = AsyncMock(spec=AsyncZR_obj)
    mock_zr.fetch_json = AsyncMock(return_value={})

    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = 'test-token'
      mock_config_class.return_value = mock_config

      rider = ZRRider()
      rider.set_session(mock_zr)
      rider.zwift_id = 12345
      rider.epoch = 1704067200

      await rider.afetch()

      # Verify endpoint includes epoch
      call_args = mock_zr.fetch_json.call_args
      assert '/public/riders/12345/1704067200' in call_args[0]


# ===============================================================================
class TestAsyncZRRiderFetchBatch:
  """Test AsyncZRRider.fetch_batch() static method."""

  @pytest.mark.anyio
  async def test_fetch_batch_empty(self):
    """Test batch fetch with no IDs returns empty dict."""
    result = await ZRRider.afetch_batch()
    assert result == {}

  @pytest.mark.anyio
  async def test_fetch_batch_max_ids(self):
    """Test batch fetch enforces 1000 ID limit."""
    ids = list(range(1001))
    with pytest.raises(ValueError, match='Maximum 1000'):
      await ZRRider.afetch_batch(*ids)

  @pytest.mark.anyio
  async def test_fetch_batch_with_mocked_session(self):
    """Test batch fetch with mocked session."""
    mock_zr = AsyncMock(spec=AsyncZR_obj)
    mock_zr.fetch_json = AsyncMock(
      return_value=[
        {
          'name': 'Rider 1',
          'gender': 'M',
          'power': {'compoundScore': 2.5},
          'race': {
            'current': {'rating': 3.2, 'mixed': {'category': 'A'}},
            'max30': {'rating': 3.5, 'mixed': {'category': 'A'}},
            'max90': {'rating': 3.0, 'mixed': {'category': 'B'}},
          },
        },
        {
          'name': 'Rider 2',
          'gender': 'F',
          'power': {'compoundScore': 2.8},
          'race': {
            'current': {'rating': 2.9, 'mixed': {'category': 'B'}},
            'max30': {'rating': 3.1, 'mixed': {'category': 'A'}},
            'max90': {'rating': 2.7, 'mixed': {'category': 'B'}},
          },
        },
      ],
    )

    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = 'test-token'
      mock_config_class.return_value = mock_config

      riders = await ZRRider.afetch_batch(12345, 67890, zr=mock_zr)

      # Verify fetch_json was called with POST method
      mock_zr.fetch_json.assert_called_once()
      call_args = mock_zr.fetch_json.call_args
      assert call_args[1]['method'] == 'POST'
      assert call_args[1]['json'] == [12345, 67890]
      assert call_args[1]['headers']['Authorization'] == 'test-token'

      # Verify we got results back
      assert len(riders) >= 1

  @pytest.mark.anyio
  async def test_fetch_batch_with_epoch(self):
    """Test batch fetch with historical epoch."""
    mock_zr = AsyncMock(spec=AsyncZR_obj)
    mock_zr.fetch_json = AsyncMock(return_value=[])

    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = 'test-token'
      mock_config_class.return_value = mock_config

      result = await ZRRider.afetch_batch(
        12345,
        67890,
        epoch=1704067200,
        zr=mock_zr,
      )

      # Verify endpoint includes epoch
      call_args = mock_zr.fetch_json.call_args
      assert '/public/riders/1704067200' in call_args[0]
      assert result == {}


# ===============================================================================
class TestAsyncZRRiderSession:
  """Test AsyncZRRider session management."""

  @pytest.mark.anyio
  async def test_set_session(self):
    """Test set_session stores the ZR object."""
    async with AsyncZR_obj() as zr:
      rider = ZRRider()
      rider.set_session(zr)
      assert rider._zr is zr

  @pytest.mark.anyio
  async def test_multiple_riders_shared_session(self):
    """Test multiple riders can share same session."""
    async with AsyncZR_obj() as zr:
      rider1 = ZRRider()
      rider2 = ZRRider()
      rider1.set_session(zr)
      rider2.set_session(zr)
      assert rider1._zr is rider2._zr
      assert rider1._zr is zr


# ===============================================================================
class TestAsyncZRRiderCloseSharedSession:
  """Test AsyncZR_obj.close_shared_session() class method."""

  @pytest.mark.anyio
  async def test_close_shared_session(self):
    """Test closing shared session."""
    from unittest.mock import AsyncMock, patch

    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      # Create an instance with shared client
      zr1 = AsyncZR_obj(shared_client=True)
      await zr1.init_client()

      # Create another instance that should use shared client
      zr2 = AsyncZR_obj(shared_client=True)
      await zr2.init_client()

      # Verify both use same shared client
      assert zr1._client is zr2._client
      # Should only create one client
      mock_client_class.assert_called_once()

      # Close shared session
      await AsyncZR_obj.close_shared_session()

      # Verify shared client is cleared
      assert AsyncZR_obj._shared_client is None
      mock_client.aclose.assert_called_once()

  @pytest.mark.anyio
  async def test_close_nonexistent_shared_session(self):
    """Test closing when no shared session exists."""
    # Should not raise error
    await AsyncZR_obj.close_shared_session()
