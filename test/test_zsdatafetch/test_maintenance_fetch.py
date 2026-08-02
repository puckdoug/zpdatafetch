"""Tests for ZSMaintenanceFetch."""

import json

import httpx2
import pytest

from zsdatafetch.zs import ZS_obj
from zsdatafetch.zsmaintenancefetch import ZSMaintenanceFetch


class TestZSMaintenanceFetch:
  """Tests for ZSMaintenanceFetch."""

  def setup_method(self):
    ZS_obj.close_client()
    ZSMaintenanceFetch.set_sync_mode(True)

  def teardown_method(self):
    ZS_obj.close_client()
    ZSMaintenanceFetch.set_sync_mode(False)

  def test_fetch_all_maintenance(self, maintenance_json):
    def handler(request):
      url = str(request.url)
      assert '/scheduled-maintenances.json' in url
      assert 'upcoming' not in url
      assert 'active' not in url
      return httpx2.Response(
        200,
        text=maintenance_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    fetcher = ZSMaintenanceFetch()
    result = fetcher.fetch()
    assert isinstance(result, list)

  def test_fetch_upcoming(self, maintenance_upcoming_json):
    def handler(request):
      assert 'upcoming.json' in str(request.url)
      return httpx2.Response(
        200,
        text=maintenance_upcoming_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    fetcher = ZSMaintenanceFetch()
    result = fetcher.fetch(upcoming=True)
    assert isinstance(result, list)

  def test_fetch_active(self, maintenance_active_json):
    def handler(request):
      assert 'active.json' in str(request.url)
      return httpx2.Response(
        200,
        text=maintenance_active_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    fetcher = ZSMaintenanceFetch()
    result = fetcher.fetch(active=True)
    assert isinstance(result, list)

  def test_empty_maintenance(self):
    empty = json.dumps(
      {'page': {}, 'scheduled_maintenances': []},
    )

    def handler(request):
      return httpx2.Response(
        200,
        text=empty,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    fetcher = ZSMaintenanceFetch()
    result = fetcher.fetch()
    assert result == []

  def test_raw(self, maintenance_json):
    def handler(request):
      return httpx2.Response(
        200,
        text=maintenance_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    fetcher = ZSMaintenanceFetch()
    fetcher.fetch()
    assert fetcher.raw() == maintenance_json

  def test_get_endpoint(self):
    assert ZSMaintenanceFetch._get_endpoint() == (
      '/scheduled-maintenances.json'
    )
    assert ZSMaintenanceFetch._get_endpoint(upcoming=True) == (
      '/scheduled-maintenances/upcoming.json'
    )
    assert ZSMaintenanceFetch._get_endpoint(active=True) == (
      '/scheduled-maintenances/active.json'
    )

  @pytest.mark.anyio
  async def test_afetch_maintenance(
    self,
    maintenance_json,
  ):
    async def handler(request):
      return httpx2.Response(
        200,
        text=maintenance_json,
        request=request,
      )

    from zsdatafetch.async_zs import AsyncZS_obj

    zs = AsyncZS_obj()
    zs._client = httpx2.AsyncClient(
      transport=httpx2.MockTransport(handler),
    )
    fetcher = ZSMaintenanceFetch()
    fetcher.set_session(zs)
    result = await fetcher.afetch()
    assert isinstance(result, list)
    await zs.close()
