"""Tests for Team with async (afetch) methods."""

import json

import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zpteamfetch import ZPTeamFetch
from zpdatafetch.zpteam import ZPTeam


@pytest.mark.anyio
async def test_async_team_fetch(login_page, logged_in_page):
  """Test AsyncTeam fetch functionality."""
  test_data = {"team_id": 123, "name": "Test Team"}

  def handler(request):
    if request.method == "GET" and "login" in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == "POST":
      return httpx.Response(200, text=logged_in_page)
    if "123_riders.json" in str(request.url):
      return httpx.Response(200, text=json.dumps(test_data))
    return httpx.Response(404)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = "testuser"
    zp.password = "testpass"
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )

    team = ZPTeamFetch()
    team.set_session(zp)
    data = await team.afetch(123)

    assert 123 in data
    assert isinstance(data[123], ZPTeam)
    assert data[123].asdict() == test_data
