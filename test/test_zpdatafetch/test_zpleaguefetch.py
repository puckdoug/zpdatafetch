"""Tests for ZPLeagueFetch class."""

import json

import httpx
import pytest

from shared.validation import ValidationError
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zpleague import ZPLeague
from zpdatafetch.zpleaguefetch import ZPLeagueFetch


def test_zpleague_empty_instantiation():
  """Test that ZPLeague can be instantiated with no arguments."""
  obj = ZPLeague()
  assert obj is not None
  assert obj.asdict() == {'league_id': 0}


def test_league(league):
  assert league is not None


def test_league_initialization(league):
  assert league._raw == {}


def test_league_init():
  """Test initialization."""
  league = ZPLeagueFetch()
  assert isinstance(league, ZPLeagueFetch)
  assert league._url_prefix == 'league_standings_'


def test_league_fetch_single_id(league, league_ok, login_page, logged_in_page):
  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'league_standings' in str(request.url) and '.json' in str(request.url):
      return httpx.Response(200, text=json.dumps(league_ok))
    return httpx.Response(404)

  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx.AsyncClient(
      follow_redirects=True,
      transport=httpx.MockTransport(handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    result = league.fetch(2780)
    assert 2780 in result
    assert isinstance(result[2780], ZPLeague)
    # Verify asdict() returns typed fields (not API format)
    asdict_result = result[2780].asdict()
    assert asdict_result['league_id'] == 2780
    assert 'standings' in asdict_result
    assert 'teams' in asdict_result
    # Verify data access through object interface
    assert result[2780]['data'][0]['name'] == 'Rider One'
  finally:
    AsyncZP.__init__ = original_init


def test_league_json_output(league, league_ok):
  league._fetched = {2780: ZPLeague(league_ok)}
  json_str = league.json()
  assert '2780' in json_str
  assert 'Rider One' in json_str


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

    league = ZPLeagueFetch()
    league.set_session(zp)

    result = await league.afetch(league_id)

    assert league_id in result
    assert isinstance(result[league_id], ZPLeague)
    assert result[league_id]['data'][0]['name'] == 'Rider One'
    # asdict() returns typed field names (not API format)
    asdict_result = league._fetched[league_id].asdict()
    assert asdict_result['league_id'] == 2780
    assert 'standings' in asdict_result
    assert 'teams' in asdict_result


@pytest.mark.anyio
async def test_league_validation():
  """Test validation."""
  league = ZPLeagueFetch()

  with pytest.raises(ValidationError):
    await league.afetch('invalid')

  with pytest.raises(ValidationError):
    await league.afetch(-1)
