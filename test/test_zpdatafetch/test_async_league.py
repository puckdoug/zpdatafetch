"""Tests for League with async (afetch) methods."""

import json

import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zpleague import ZPLeague
from zpdatafetch.zpleaguefetch import ZPLeagueFetch


@pytest.mark.anyio
async def test_async_league_fetch(league_ok, login_page, logged_in_page):
  """Test async league fetch functionality."""

  def handler(request):
    if request.method == "GET" and "login" in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == "POST":
      return httpx.Response(200, text=logged_in_page)
    if "league_standings_2780.json" in str(request.url):
      return httpx.Response(200, text=json.dumps(league_ok))
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

    league = ZPLeagueFetch()
    league.set_session(zp)
    data = await league.afetch(2780)

    assert 2780 in data
    assert isinstance(data[2780], ZPLeague)

    # Verify asdict returns typed field names (not API format)
    result = data[2780].asdict()
    assert result["league_id"] == 2780
    assert "standings" in result  # Not 'data'
    assert "teams" in result

    # Verify team uses typed field names
    team = result["teams"]["1"]
    assert team["name"] == "Test Team"
    assert team["color_background"] == "ffffff"
    assert team["color_border"] == "000000"
    assert team["color_text"] == "ffffff"

    # Verify standings use typed field names
    standing = result["standings"][0]
    assert standing["position"] == 1  # Not 'pos'
    assert standing["zwift_id"] == 123456  # Not 'zwid'
    assert standing["team_id"] == 1  # Not 'tid'
    assert standing["team_name"] == "Test Team"  # Resolved team name
    assert standing["name"] == "Rider One"
    assert standing["points"] == 100
    assert standing["events"] == 5
    assert standing["category"] == "A"
