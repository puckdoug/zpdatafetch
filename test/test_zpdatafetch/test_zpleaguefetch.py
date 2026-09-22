"""Tests for ZPLeagueFetch class."""

import json

import httpx2
import pytest

from shared.validation import ValidationError
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zpleague import ZPLeague, ZPLeagueEvent
from zpdatafetch.zpleaguefetch import ZPLeagueFetch


def test_zpleague_empty_instantiation():
  """Test that ZPLeague can be instantiated with no arguments."""
  obj = ZPLeague()
  assert obj is not None
  assert obj.asdict() == {'league_id': 0}


def test_zpleague_event_parse_full_fixture():
  """Parse all events from the real league-3379 fixture."""

  with open('test/fixtures/league_event_results_3379.json', encoding='utf-8') as f:
    data = json.load(f)
  events = [ZPLeagueEvent.from_dict(e) for e in data['data']]
  assert len(events) == 530

# Typed fields - first event is the Women variant of the named stage
  assert events[0].event_id == 5695925
  assert events[0].title == 'Stage 3 - ZRacing - DURA-ACE - Electric Break | Women'

  # Find an exact (non-Women) match for the named event
  exact = next(e for e in events if e.title == 'Stage 3 - ZRacing - DURA-ACE - Electric Break')
  assert exact.event_id == 5695126

  start = exact.start_datetime
  assert isinstance(start, int) and start == 1790032200

  # Extras capture untyped fields
  assert exact.extras()['km'] == 19599

  # Excluded holds recognized-but-untyped fields
  assert 'DT_RowId' in exact.excluded()


def test_zpleague_event_parse_no_results_fixture():
  """Parse the events-only league-3388 fixture (no results arrays)."""

  with open('test/fixtures/league_event_results_3388.json', encoding='utf-8') as f:
    data = json.load(f)
  events = [ZPLeagueEvent.from_dict(e) for e in data['data']]
  assert len(events) == 12
  assert events[0].title.startswith('Sykkelkomponenter Pain Cave Ultra by 5071 Cykleklubb - Round ')  # whitespace-robust
  assert '12/12' in events[0].title

  # No results key - excluded stays empty, extras has the rest
  assert 'results' not in events[0].excluded()
  assert events[0].extras()['km'] == 23670


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
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'league_standings' in str(request.url) and '.json' in str(request.url):
      return httpx2.Response(200, text=json.dumps(league_ok))
    return httpx2.Response(404)

  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx2.AsyncClient(
      follow_redirects=True,
      transport=httpx2.MockTransport(handler),
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
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'league_standings_2780.json' in str(request.url):
      return httpx2.Response(200, text=json.dumps(league_ok))
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
