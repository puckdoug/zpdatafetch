"""Tests for ZRResult class with async (afetch) methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.zrresult import ZRResult


# ===============================================================================
class TestAsyncZRResultFetch:
  """Test ZRResult.afetch() method."""

  @pytest.mark.anyio
  async def test_fetch_no_race_id(self):
    """Test fetch with no race_id returns silently."""
    async with AsyncZR_obj() as zr:
      result = ZRResult()
      result.set_session(zr)
      # Should return without error when race_id is 0
      await result.afetch()
      assert result.race_id == 0

  @pytest.mark.anyio
  async def test_fetch_parses_response(self):
    """Test that fetch with valid data parses response."""
    async with AsyncZR_obj() as zr:
      result = ZRResult()
      result.set_session(zr)
      # Mock response by directly setting _raw
      result._raw = [
        {
          'riderId': 12345,
          'position': 1,
          'positionInCategory': 1,
          'category': 'A',
          'time': 3600.0,
          'gap': 0.0,
          'ratingBefore': 3.2,
          'rating': 3.5,
          'ratingDelta': 0.3,
        },
        {
          'riderId': 67890,
          'position': 2,
          'positionInCategory': 2,
          'category': 'A',
          'time': 3605.0,
          'gap': 5.0,
          'ratingBefore': 2.8,
          'rating': 3.0,
          'ratingDelta': 0.2,
        },
      ]
      result.race_id = 3590800
      result._parse_response()
      assert len(result.results) == 2
      assert result.results[0].zwift_id == 12345
      assert result.results[0].position == 1

  @pytest.mark.anyio
  async def test_fetch_handles_empty_response(self):
    """Test fetch handles empty response list."""
    async with AsyncZR_obj() as zr:
      result = ZRResult()
      result.set_session(zr)
      result._raw = []
      result.race_id = 3590800
      result._parse_response()
      assert len(result.results) == 0

  @pytest.mark.anyio
  async def test_fetch_handles_malformed_response(self):
    """Test fetch handles malformed rider data."""
    async with AsyncZR_obj() as zr:
      result = ZRResult()
      result.set_session(zr)
      result._raw = [
        {
          'riderId': 12345,
          'position': 1,
          # Missing other fields - should still parse with defaults
          'ratingBefore': 3.2,
        },
      ]
      result.race_id = 3590800
      result._parse_response()
      assert len(result.results) == 1

  @pytest.mark.anyio
  async def test_fetch_with_mocked_session(self):
    """Test fetch with mocked session."""
    mock_zr = AsyncMock(spec=AsyncZR_obj)
    mock_zr.fetch_json = AsyncMock(
      return_value=[
        {
          'riderId': 12345,
          'position': 1,
          'positionInCategory': 1,
          'category': 'A',
          'time': 3600.0,
          'gap': 0.0,
          'ratingBefore': 3.2,
          'rating': 3.5,
          'ratingDelta': 0.3,
        },
      ],
    )

    with patch('zrdatafetch.zrresult.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = 'test-token'
      mock_config_class.return_value = mock_config

      result = ZRResult()
      result.set_session(mock_zr)
      result.race_id = 3590800

      await result.afetch()

      # Verify fetch_json was called with correct endpoint and headers
      mock_zr.fetch_json.assert_called_once()
      call_args = mock_zr.fetch_json.call_args
      assert '/public/results/3590800' in call_args[0]
      assert call_args[1]['headers']['Authorization'] == 'test-token'

      # Verify data was parsed
      assert len(result.results) == 1
      assert result.results[0].zwift_id == 12345

  @pytest.mark.anyio
  async def test_async_context_manager(self):
    """Test AsyncZRResult works with async context manager."""
    async with AsyncZR_obj() as zr:
      result = ZRResult()
      result.set_session(zr)
      assert result._zr is zr


# ===============================================================================
class TestAsyncZRResultSession:
  """Test AsyncZRResult session management."""

  @pytest.mark.anyio
  async def test_set_session(self):
    """Test set_session stores the ZR object."""
    async with AsyncZR_obj() as zr:
      result = ZRResult()
      result.set_session(zr)
      assert result._zr is zr

  @pytest.mark.anyio
  async def test_multiple_results_shared_session(self):
    """Test multiple results can share same session."""
    async with AsyncZR_obj() as zr:
      result1 = ZRResult()
      result2 = ZRResult()
      result1.set_session(zr)
      result2.set_session(zr)
      assert result1._zr is result2._zr
      assert result1._zr is zr
