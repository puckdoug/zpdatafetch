"""Tests for League class."""

import json
import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.league import League
from shared.validation import ValidationError


@pytest.fixture
def league_ok():
  return {'data': [{'div': 1, 'name': 'Rider One', 'team_name': 'Test Team'}]}


def test_league_init():
  """Test initialization."""
  league = League()
  assert isinstance(league, League)
  assert league._url_prefix == 'league_standings_'


@pytest.mark.anyio
async def test_league_afetch(league_ok, login_page, logged_in_page):
  """Test asynchronous fetch using MockTransport."""
  league_id = 2780

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

    result = await league.afetch(league_id)

    assert league_id in result
    assert result[league_id]['data'][0]['name'] == 'Rider One'
    assert league.processed[league_id] == league_ok


@pytest.mark.anyio
async def test_league_validation():
  """Test validation."""
  league = League()

  with pytest.raises(ValidationError):
    await league.afetch('invalid')

  with pytest.raises(ValidationError):
    await league.afetch(-1)
