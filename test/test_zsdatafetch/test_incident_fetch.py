"""Tests for ZSIncidentFetch."""

import httpx
import pytest

from zsdatafetch.models.incident import ZSIncident
from zsdatafetch.zs import ZS_obj
from zsdatafetch.zsincidentfetch import ZSIncidentFetch


class TestZSIncidentFetch:
  """Tests for ZSIncidentFetch."""

  def setup_method(self):
    ZS_obj.close_client()
    ZSIncidentFetch.set_sync_mode(True)

  def teardown_method(self):
    ZS_obj.close_client()
    ZSIncidentFetch.set_sync_mode(False)

  def test_fetch_all_incidents(self, incidents_json):
    def handler(request):
      assert '/incidents.json' in str(request.url)
      assert 'unresolved' not in str(request.url)
      return httpx.Response(
        200, text=incidents_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSIncidentFetch()
    result = fetcher.fetch()
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(i, ZSIncident) for i in result)

  def test_fetch_unresolved(self, incidents_unresolved_json):
    def handler(request):
      assert '/incidents/unresolved.json' in str(request.url)
      return httpx.Response(
        200,
        text=incidents_unresolved_json,
        request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSIncidentFetch()
    result = fetcher.fetch(unresolved_only=True)
    assert isinstance(result, list)

  def test_empty_incidents(self):
    import json
    empty = json.dumps({'page': {}, 'incidents': []})

    def handler(request):
      return httpx.Response(
        200, text=empty, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSIncidentFetch()
    result = fetcher.fetch()
    assert result == []

  def test_raw(self, incidents_json):
    def handler(request):
      return httpx.Response(
        200, text=incidents_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSIncidentFetch()
    fetcher.fetch()
    assert fetcher.raw() == incidents_json

  def test_fetched(self, incidents_json):
    def handler(request):
      return httpx.Response(
        200, text=incidents_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSIncidentFetch()
    assert fetcher.fetched() == []
    fetcher.fetch()
    assert len(fetcher.fetched()) > 0

  @pytest.mark.anyio
  async def test_afetch_incidents(self, incidents_json):
    async def handler(request):
      return httpx.Response(
        200, text=incidents_json, request=request,
      )

    from zsdatafetch.async_zs import AsyncZS_obj
    zs = AsyncZS_obj()
    zs._client = httpx.AsyncClient(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSIncidentFetch()
    fetcher.set_session(zs)
    result = await fetcher.afetch()
    assert isinstance(result, list)
    assert len(result) > 0
    await zs.close()
