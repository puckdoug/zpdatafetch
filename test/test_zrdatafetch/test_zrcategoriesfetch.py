"""Tests for ZRCategoriesFetch using httpx2.MockTransport."""

from pathlib import Path
from unittest.mock import patch

import httpx2
import pytest

from shared.exceptions import ConfigError
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrcategories import ZRCategories
from zrdatafetch.zrcategoriesfetch import ZRCategoriesFetch

FIXTURE_PATH = Path(__file__).parent.parent / 'fixtures' / 'zr_categories.json'


@pytest.fixture
def fixture_json() -> str:
  """Raw fixture JSON text (as the server would return it)."""
  with open(FIXTURE_PATH, encoding='utf-8') as f:
    return f.read()


@pytest.fixture(autouse=True)
def reset_sync_mode():
  """Reset ZRCategoriesFetch class-level sync mode between tests."""
  yield
  ZRCategoriesFetch.set_sync_mode(False)


@pytest.fixture
def captured():
  """Shared dict capturing request url and headers from the transport."""
  return {}


@pytest.fixture
def install_mock_client(captured):
  """Factory installing a MockTransport-backed shared client on ZR_obj."""
  original = ZR_obj._client
  installed = []

  def _install(body: str) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
      captured['url'] = request.url
      captured['headers'] = dict(request.headers)
      return httpx2.Response(200, text=body)

    client = httpx2.Client(
      base_url=ZR_obj._base_url,
      transport=httpx2.MockTransport(handler),
    )
    ZR_obj._client = client
    installed.append(client)

  yield _install
  for client in installed:
    client.close()
  ZR_obj._client = original


class TestZRCategoriesFetchSync:
  """Test the synchronous fetch path (sync mode)."""

  def test_fetch_returns_zrcategories(self, install_mock_client, fixture_json):
    install_mock_client(fixture_json)
    ZRCategoriesFetch.set_sync_mode(True)
    fetcher = ZRCategoriesFetch()
    result = fetcher.fetch()
    assert isinstance(result, ZRCategories)
    assert result.scale == '1-1000'
    assert len(result.categories) == 10

  def test_fetch_sends_authorization_header(
    self, install_mock_client, fixture_json, captured,
  ):
    install_mock_client(fixture_json)
    ZRCategoriesFetch.set_sync_mode(True)
    fetcher = ZRCategoriesFetch()
    fetcher.fetch()
    assert captured['headers'].get('authorization') == 'test_auth_token'

  def test_fetch_requests_v2_categories_endpoint(
    self, install_mock_client, fixture_json, captured,
  ):
    install_mock_client(fixture_json)
    ZRCategoriesFetch.set_sync_mode(True)
    fetcher = ZRCategoriesFetch()
    fetcher.fetch()
    assert (
      str(captured['url'])
      == 'https://api.zwiftracing.app/api/v2/public/categories'
    )

  def test_fetch_stores_raw_and_fetched(self, install_mock_client, fixture_json):
    install_mock_client(fixture_json)
    ZRCategoriesFetch.set_sync_mode(True)
    fetcher = ZRCategoriesFetch()
    fetcher.fetch()
    assert fetcher.raw() == {0: fixture_json}
    assert isinstance(fetcher.fetched()[0], ZRCategories)

  def test_fetch_malformed_response_returns_empty(self, install_mock_client):
    install_mock_client('["unexpected"]')
    ZRCategoriesFetch.set_sync_mode(True)
    fetcher = ZRCategoriesFetch()
    result = fetcher.fetch()
    assert isinstance(result, ZRCategories)
    assert result.scale == ''
    assert result.categories == []
    assert isinstance(fetcher.fetched()[0], ZRCategories)


class TestZRCategoriesFetchAsync:
  """Test the asynchronous fetch path."""

  @pytest.mark.anyio
  async def test_afetch_returns_zrcategories(
    self, fixture_json, captured,
  ):
    def handler(request: httpx2.Request) -> httpx2.Response:
      captured['url'] = request.url
      captured['headers'] = dict(request.headers)
      return httpx2.Response(200, text=fixture_json)

    zr = AsyncZR_obj()
    zr._client = httpx2.AsyncClient(
      base_url=AsyncZR_obj._base_url,
      transport=httpx2.MockTransport(handler),
    )
    fetcher = ZRCategoriesFetch()
    fetcher.set_session(zr)
    result = await fetcher.afetch()
    await zr.close()
    assert isinstance(result, ZRCategories)
    assert result.scale == '1-1000'
    assert len(result.categories) == 10
    assert captured['headers'].get('authorization') == 'test_auth_token'

  @pytest.mark.anyio
  async def test_afetch_missing_authorization_raises(self):
    with patch('zrdatafetch.zrcategoriesfetch.Config') as mock_config:
      mock_config.return_value.authorization = ''
      fetcher = ZRCategoriesFetch()
      with pytest.raises(ConfigError):
        await fetcher.afetch()


class TestZRCategoriesFetchConfigError:
  """Test the missing-authorization error."""

  def test_fetch_sync_missing_authorization_raises(self):
    ZRCategoriesFetch.set_sync_mode(True)
    with patch('zrdatafetch.zrcategoriesfetch.Config') as mock_config:
      mock_config.return_value.authorization = ''
      fetcher = ZRCategoriesFetch()
      with pytest.raises(ConfigError):
        fetcher.fetch()
