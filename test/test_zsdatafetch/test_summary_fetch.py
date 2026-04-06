"""Tests for ZSSummaryFetch."""

import json

import httpx
import pytest

from zsdatafetch.models.summary import ZSSummary
from zsdatafetch.zs import ZS_obj
from zsdatafetch.zssummaryfetch import ZSSummaryFetch


class TestZSSummaryFetch:
  """Tests for ZSSummaryFetch."""

  def setup_method(self):
    ZS_obj.close_client()
    ZSSummaryFetch.set_sync_mode(True)

  def teardown_method(self):
    ZS_obj.close_client()
    ZSSummaryFetch.set_sync_mode(False)

  def test_fetch_summary(self, summary_json):
    def handler(request):
      assert '/summary.json' in str(request.url)
      return httpx.Response(
        200, text=summary_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSSummaryFetch()
    result = fetcher.fetch()
    assert isinstance(result, ZSSummary)
    assert result.page.name == 'Zwift, Inc'
    assert result.status.indicator == 'none'
    assert len(result.components) > 0

  def test_fetch_components_only(self, components_json):
    def handler(request):
      assert '/components.json' in str(request.url)
      return httpx.Response(
        200, text=components_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSSummaryFetch()
    result = fetcher.fetch(components_only=True)
    assert isinstance(result, ZSSummary)
    assert len(result.components) > 0

  def test_fetch_raw(self, summary_json):
    def handler(request):
      return httpx.Response(
        200, text=summary_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSSummaryFetch()
    fetcher.fetch()
    raw = fetcher.raw()
    assert raw == summary_json

  def test_fetched(self, summary_json):
    def handler(request):
      return httpx.Response(
        200, text=summary_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSSummaryFetch()
    assert fetcher.fetched() is None
    fetcher.fetch()
    assert fetcher.fetched() is not None

  def test_json_output(self, summary_json):
    def handler(request):
      return httpx.Response(
        200, text=summary_json, request=request,
      )

    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSSummaryFetch()
    fetcher.fetch()
    result_json = fetcher.json()
    parsed = json.loads(result_json)
    assert 'page' in parsed
    assert 'status' in parsed

  def test_sync_mode(self, summary_json):
    def handler(request):
      return httpx.Response(
        200, text=summary_json, request=request,
      )

    ZSSummaryFetch.set_sync_mode(True)
    ZS_obj._client = httpx.Client(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSSummaryFetch()
    result = fetcher.fetch()
    assert isinstance(result, ZSSummary)

  @pytest.mark.anyio
  async def test_afetch_summary(self, summary_json):
    async def handler(request):
      return httpx.Response(
        200, text=summary_json, request=request,
      )

    from zsdatafetch.async_zs import AsyncZS_obj
    zs = AsyncZS_obj()
    zs._client = httpx.AsyncClient(
      transport=httpx.MockTransport(handler),
    )
    fetcher = ZSSummaryFetch()
    fetcher.set_session(zs)
    result = await fetcher.afetch()
    assert isinstance(result, ZSSummary)
    assert result.page.name == 'Zwift, Inc'
    await zs.close()
