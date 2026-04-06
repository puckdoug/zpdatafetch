"""Tests for ZS_obj and AsyncZS_obj base classes."""

import json

import httpx
import pytest

from shared.exceptions import NetworkError
from zsdatafetch.async_zs import AsyncZS_obj
from zsdatafetch.zs import ZS_obj


class TestZSObj:
  """Tests for ZS_obj synchronous base class."""

  def setup_method(self):
    ZS_obj.close_client()

  def teardown_method(self):
    ZS_obj.close_client()

  def test_get_client_creates_shared_client(self):
    client = ZS_obj.get_client()
    assert client is not None
    assert isinstance(client, httpx.Client)
    # Second call returns same instance
    assert ZS_obj.get_client() is client

  def test_close_client(self):
    ZS_obj.get_client()
    assert ZS_obj._client is not None
    ZS_obj.close_client()
    assert ZS_obj._client is None

  def test_close_client_when_none(self):
    ZS_obj._client = None
    ZS_obj.close_client()  # Should not raise
    assert ZS_obj._client is None

  def test_fetch_json_success(self):
    test_data = {'status': {'indicator': 'none'}}

    def handler(request):
      return httpx.Response(
        200,
        text=json.dumps(test_data),
        request=request,
      )

    obj = ZS_obj()
    # Replace the client with a mock transport
    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    result = obj.fetch_json('/summary.json')
    assert json.loads(result) == test_data

  def test_fetch_json_http_error(self):
    def handler(request):
      return httpx.Response(
        500,
        text='Internal Server Error',
        request=request,
      )

    obj = ZS_obj()
    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    with pytest.raises(NetworkError):
      obj.fetch_json('/summary.json')

  def test_fetch_json_network_error(self):
    def handler(request):
      raise httpx.ConnectError('Connection refused')

    obj = ZS_obj()
    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    with pytest.raises(NetworkError):
      obj.fetch_json('/summary.json')


class TestAsyncZSObj:
  """Tests for AsyncZS_obj async base class."""

  @pytest.mark.anyio
  async def test_async_fetch_json_success(self):
    test_data = {'status': {'indicator': 'none'}}

    async def handler(request):
      return httpx.Response(
        200,
        text=json.dumps(test_data),
        request=request,
      )

    obj = AsyncZS_obj()
    obj._client = httpx.AsyncClient(
      transport=httpx.MockTransport(handler),
    )
    result = await obj.fetch_json('/summary.json')
    assert json.loads(result) == test_data
    await obj.close()

  @pytest.mark.anyio
  async def test_async_fetch_json_error(self):
    async def handler(request):
      return httpx.Response(
        500,
        text='Error',
        request=request,
      )

    obj = AsyncZS_obj()
    obj._client = httpx.AsyncClient(
      transport=httpx.MockTransport(handler),
    )
    with pytest.raises(NetworkError):
      await obj.fetch_json('/summary.json')
    await obj.close()

  @pytest.mark.anyio
  async def test_async_context_manager(self):
    async with AsyncZS_obj() as zs:
      assert zs._client is not None
    assert zs._client is None

  @pytest.mark.anyio
  async def test_init_client(self):
    obj = AsyncZS_obj()
    assert obj._client is None
    await obj.init_client()
    assert obj._client is not None
    await obj.close()
