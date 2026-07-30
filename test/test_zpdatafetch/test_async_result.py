"""Tests for Result with async (afetch) methods."""

import json

import httpx2
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zpraceresult import ZPRaceResult
from zpdatafetch.zpresultfetch import ZPResultFetch


@pytest.mark.anyio
async def test_async_result_fetch(login_page, logged_in_page):
  """Test AsyncResult fetch functionality."""
  test_data = {'race_id': 3590800, 'results': []}

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if '3590800' in str(request.url):
      return httpx2.Response(200, text=json.dumps(test_data))
    return httpx2.Response(404)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx2.AsyncClient(
        follow_redirects=True,
        transport=httpx2.MockTransport(handler),
      ),
    )

    result = ZPResultFetch()
    result.set_session(zp)
    data = await result.afetch(3590800)

    assert 3590800 in data
    assert isinstance(data[3590800], ZPRaceResult)
    # Verify structure: should have race_id and data array
    result_dict = data[3590800].asdict()
    assert result_dict['race_id'] == 3590800
    assert 'data' in result_dict
    # Verify extra fields are captured via extras() method (not in asdict)
    assert 'results' in data[3590800].extras()
