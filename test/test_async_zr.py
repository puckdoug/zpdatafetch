"""Tests for AsyncZR_obj base class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zrdatafetch.async_zr import AsyncZR_obj


# ===============================================================================
class TestAsyncZRObjInitialization:
  """Test AsyncZR_obj initialization."""

  def test_init_default(self):
    """Test default initialization."""
    zr = AsyncZR_obj()
    assert zr._client is None
    assert zr._owns_client is True

  def test_init_shared_client_false(self):
    """Test initialization with shared_client=False."""
    zr = AsyncZR_obj(shared_client=False)
    assert zr._owns_client is True

  @pytest.mark.anyio
  async def test_init_shared_client_true(self):
    """Test initialization with shared_client=True."""
    # Mock AsyncClient to prevent real connections
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj(shared_client=True)
      assert zr._owns_client is False
      # Cleanup shared client
      await AsyncZR_obj.close_shared_session()


# ===============================================================================
class TestAsyncZRObjContextManager:
  """Test AsyncZR_obj as async context manager."""

  @pytest.mark.anyio
  async def test_context_manager_aenter(self):
    """Test __aenter__ returns self."""
    async with AsyncZR_obj() as zr:
      assert isinstance(zr, AsyncZR_obj)

  @pytest.mark.anyio
  async def test_context_manager_aexit(self):
    """Test __aexit__ properly cleans up."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      await zr.init_client()
      result = await zr.__aexit__(None, None, None)
      assert result is False  # Should return False to propagate exceptions
      mock_client.aclose.assert_called_once()

  @pytest.mark.anyio
  async def test_context_manager_cleanup(self):
    """Test context manager properly closes client."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      async with AsyncZR_obj() as zr:
        await zr.init_client()
        assert zr._client is not None
      # After exit, close should have been called
      mock_client.aclose.assert_called_once()


# ===============================================================================
class TestAsyncZRObjClientInitialization:
  """Test AsyncZR_obj client initialization."""

  @pytest.mark.anyio
  async def test_init_client_creates_new(self):
    """Test init_client creates a new client."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      await zr.init_client()
      assert zr._client is mock_client
      mock_client_class.assert_called_once()

  @pytest.mark.anyio
  async def test_init_client_with_provided_client(self):
    """Test init_client accepts provided client."""
    mock_client = AsyncMock()

    zr = AsyncZR_obj()
    await zr.init_client(client=mock_client)
    assert zr._client is mock_client

  @pytest.mark.anyio
  async def test_init_client_uses_shared(self):
    """Test init_client uses shared client when available."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr1 = AsyncZR_obj(shared_client=True)
      await zr1.init_client()

      zr2 = AsyncZR_obj(shared_client=True)
      await zr2.init_client()

      # Both should use same shared client
      assert zr1._client is zr2._client
      # Should only create client once
      mock_client_class.assert_called_once()

      await AsyncZR_obj.close_shared_session()


# ===============================================================================
class TestAsyncZRObjFetchJson:
  """Test AsyncZR_obj.fetch_json() method."""

  @pytest.mark.anyio
  async def test_fetch_json_initializes_client(self):
    """Test fetch_json initializes client if needed."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_response = MagicMock()
      mock_response.json.return_value = {'test': 'data'}
      mock_client.request.return_value = mock_response
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      assert zr._client is None

      result = await zr.fetch_json('/test')

      # Client should have been initialized
      assert zr._client is not None
      assert result == {'test': 'data'}

  @pytest.mark.anyio
  async def test_fetch_json_returns_dict(self):
    """Test fetch_json returns dict for JSON response."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_response = MagicMock()
      mock_response.json.return_value = {'id': 12345, 'name': 'Test Rider'}
      mock_client.request.return_value = mock_response
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      result = await zr.fetch_json('/public/riders/12345')

      assert result == {'id': 12345, 'name': 'Test Rider'}
      mock_client.request.assert_called_once()

  @pytest.mark.anyio
  async def test_fetch_json_with_method_post(self):
    """Test fetch_json supports POST method."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_response = MagicMock()
      mock_response.json.return_value = [{'id': 12345}, {'id': 67890}]
      mock_client.request.return_value = mock_response
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      result = await zr.fetch_json(
        '/public/riders',
        method='POST',
        json=[12345, 67890],
      )

      assert result == [{'id': 12345}, {'id': 67890}]
      # Verify POST was used
      call_args = mock_client.request.call_args
      assert call_args[0][0] == 'POST' or call_args.kwargs.get('method') == 'POST'

  @pytest.mark.anyio
  async def test_fetch_json_with_headers(self):
    """Test fetch_json accepts headers."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_response = MagicMock()
      mock_response.json.return_value = {'id': 12345}
      mock_client.request.return_value = mock_response
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      result = await zr.fetch_json(
        '/public/riders/12345',
        headers={'Authorization': 'token'},
      )

      assert result == {'id': 12345}
      # Verify headers were passed
      call_args = mock_client.request.call_args
      assert 'Authorization' in (call_args.kwargs.get('headers', {}) or {})


# ===============================================================================
class TestAsyncZRObjClose:
  """Test AsyncZR_obj.close() method."""

  @pytest.mark.anyio
  async def test_close_owned_client(self):
    """Test close properly closes owned client."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      await zr.init_client()
      assert zr._owns_client is True
      assert zr._client is not None

      await zr.close()
      mock_client.aclose.assert_called_once()

  @pytest.mark.anyio
  async def test_close_shared_client(self):
    """Test close doesn't close shared client."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj(shared_client=True)
      await zr.init_client()
      assert zr._owns_client is False

      # Close should not actually close the shared client
      await zr.close()

      # Shared client should still exist
      assert AsyncZR_obj._shared_client is not None
      # aclose should NOT have been called
      mock_client.aclose.assert_not_called()

      await AsyncZR_obj.close_shared_session()

  @pytest.mark.anyio
  async def test_close_idempotent(self):
    """Test close can be called multiple times safely."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj()
      await zr.init_client()
      await zr.close()
      await zr.close()  # Should not raise

      # The implementation may call aclose multiple times, which is fine
      # The important thing is that it doesn't raise an error
      assert mock_client.aclose.call_count >= 1


# ===============================================================================
class TestAsyncZRObjSharedSession:
  """Test AsyncZR_obj shared session management."""

  @pytest.mark.anyio
  async def test_close_shared_session_clears_reference(self):
    """Test close_shared_session clears the shared client."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr = AsyncZR_obj(shared_client=True)
      await zr.init_client()
      assert AsyncZR_obj._shared_client is not None

      await AsyncZR_obj.close_shared_session()
      assert AsyncZR_obj._shared_client is None
      mock_client.aclose.assert_called_once()

  @pytest.mark.anyio
  async def test_close_shared_session_idempotent(self):
    """Test close_shared_session can be called multiple times."""
    await AsyncZR_obj.close_shared_session()  # First call
    await AsyncZR_obj.close_shared_session()  # Second call - should not raise

  @pytest.mark.anyio
  async def test_multiple_instances_share_client(self):
    """Test multiple instances with shared_client=True share the same client."""
    with patch('httpx.AsyncClient') as mock_client_class:
      mock_client = AsyncMock()
      mock_client_class.return_value = mock_client

      zr1 = AsyncZR_obj(shared_client=True)
      await zr1.init_client()
      client1 = zr1._client

      zr2 = AsyncZR_obj(shared_client=True)
      await zr2.init_client()
      client2 = zr2._client

      assert client1 is client2
      # Should only create one client
      mock_client_class.assert_called_once()

      await AsyncZR_obj.close_shared_session()
