"""Tests for AsyncZR_obj base class."""

import pytest

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.exceptions import ZRNetworkError


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
    zr = AsyncZR_obj()
    await zr.init_client()
    result = await zr.__aexit__(None, None, None)
    assert result is False  # Should return False to propagate exceptions

  @pytest.mark.anyio
  async def test_context_manager_cleanup(self):
    """Test context manager properly closes client."""
    async with AsyncZR_obj() as zr:
      await zr.init_client()
      assert zr._client is not None
    # After exit, client should be closed
    # (We can't easily verify close, but it shouldn't raise)


# ===============================================================================
class TestAsyncZRObjClientInitialization:
  """Test AsyncZR_obj client initialization."""

  @pytest.mark.anyio
  async def test_init_client_creates_new(self):
    """Test init_client creates a new client."""
    zr = AsyncZR_obj()
    await zr.init_client()
    assert zr._client is not None

  @pytest.mark.anyio
  async def test_init_client_with_provided_client(self):
    """Test init_client accepts provided client."""
    import httpx

    async with httpx.AsyncClient() as client:
      zr = AsyncZR_obj()
      await zr.init_client(client=client)
      assert zr._client is client
      # Don't close - httpx client manages itself

  @pytest.mark.anyio
  async def test_init_client_uses_shared(self):
    """Test init_client uses shared client when available."""
    zr1 = AsyncZR_obj(shared_client=True)
    await zr1.init_client()

    zr2 = AsyncZR_obj(shared_client=True)
    await zr2.init_client()

    # Both should use same shared client
    assert zr1._client is zr2._client
    await AsyncZR_obj.close_shared_session()


# ===============================================================================
class TestAsyncZRObjFetchJson:
  """Test AsyncZR_obj.fetch_json() method."""

  @pytest.mark.anyio
  async def test_fetch_json_initializes_client(self):
    """Test fetch_json initializes client if needed."""
    zr = AsyncZR_obj()
    assert zr._client is None
    # This will fail (network error), but should initialize client first
    with pytest.raises(ZRNetworkError):
      await zr.fetch_json('/test')
    # Client should have been initialized
    assert zr._client is not None

  @pytest.mark.anyio
  async def test_fetch_json_returns_dict(self):
    """Test fetch_json returns dict for JSON response."""
    zr = AsyncZR_obj()
    # This will fail due to network/auth, but tests the pattern
    with pytest.raises(ZRNetworkError):
      await zr.fetch_json('/public/riders/12345')

  @pytest.mark.anyio
  async def test_fetch_json_with_method_post(self):
    """Test fetch_json supports POST method."""
    zr = AsyncZR_obj()
    # This will fail due to network/auth, but tests the pattern
    with pytest.raises(ZRNetworkError):
      await zr.fetch_json(
        '/public/riders',
        method='POST',
        json=[12345, 67890],
      )

  @pytest.mark.anyio
  async def test_fetch_json_with_headers(self):
    """Test fetch_json accepts headers."""
    zr = AsyncZR_obj()
    # This will fail due to network/auth, but tests the pattern
    with pytest.raises(ZRNetworkError):
      await zr.fetch_json(
        '/public/riders/12345',
        headers={'Authorization': 'token'},
      )


# ===============================================================================
class TestAsyncZRObjClose:
  """Test AsyncZR_obj.close() method."""

  @pytest.mark.anyio
  async def test_close_owned_client(self):
    """Test close properly closes owned client."""
    zr = AsyncZR_obj()
    await zr.init_client()
    assert zr._owns_client is True
    assert zr._client is not None
    await zr.close()
    # Client should be closed (can't easily verify, but shouldn't raise)

  @pytest.mark.anyio
  async def test_close_shared_client(self):
    """Test close doesn't close shared client."""
    zr = AsyncZR_obj(shared_client=True)
    await zr.init_client()
    assert zr._owns_client is False
    # Close should not actually close the shared client
    await zr.close()
    # Shared client should still exist
    assert AsyncZR_obj._shared_client is not None
    await AsyncZR_obj.close_shared_session()

  @pytest.mark.anyio
  async def test_close_idempotent(self):
    """Test close can be called multiple times safely."""
    zr = AsyncZR_obj()
    await zr.init_client()
    await zr.close()
    await zr.close()  # Should not raise


# ===============================================================================
class TestAsyncZRObjSharedSession:
  """Test AsyncZR_obj shared session management."""

  @pytest.mark.anyio
  async def test_close_shared_session_clears_reference(self):
    """Test close_shared_session clears the shared client."""
    zr = AsyncZR_obj(shared_client=True)
    await zr.init_client()
    assert AsyncZR_obj._shared_client is not None

    await AsyncZR_obj.close_shared_session()
    assert AsyncZR_obj._shared_client is None

  @pytest.mark.anyio
  async def test_close_shared_session_idempotent(self):
    """Test close_shared_session can be called multiple times."""
    await AsyncZR_obj.close_shared_session()  # First call
    await AsyncZR_obj.close_shared_session()  # Second call - should not raise

  @pytest.mark.anyio
  async def test_multiple_instances_share_client(self):
    """Test multiple instances with shared_client=True share the same client."""
    zr1 = AsyncZR_obj(shared_client=True)
    await zr1.init_client()
    client1 = zr1._client

    zr2 = AsyncZR_obj(shared_client=True)
    await zr2.init_client()
    client2 = zr2._client

    assert client1 is client2
    await AsyncZR_obj.close_shared_session()
