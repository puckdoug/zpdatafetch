"""Tests for League with async (afetch) methods."""

import json

import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.league import League


@pytest.mark.anyio
async def test_async_league_fetch(league_ok, login_page, logged_in_page):
  """Test async league fetch functionality."""

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'league_standings_2780.json' in str(request.url):
      return httpx.Response(200, text=json.dumps(league_ok))
    return httpx.Response(404)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )

    league = League()
    league.set_session(zp)
    data = await league.afetch(2780)

    assert 2780 in data
    assert data[2780] == league_ok
