"""Tests for ZPLeagueFetch class."""

import json

import httpx2
import pytest

from shared.validation import ValidationError
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zp import ZP
from zpdatafetch.zpleague import (
  ZPLeague,
  ZPLeagueEvent,
  ZPLeagueInfo,
  ZPLeagueTeamEventResult,
  ZPLeagueTeamStanding,
)
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


def test_zpleague_team_standings_parse_fixture():
  """Parse team standings from the real league-3379 fixture."""

  with open('test/fixtures/league_team_standings_3379.json', encoding='utf-8') as f:
    data = json.load(f)
  rows = [ZPLeagueTeamStanding.from_dict(r) for r in data['data']]
  assert len(rows) == 2685

  # Typed fields on the top row
  assert rows[0].team_id == 16219
  assert rows[0].team_name == 'SISU Racing'
  assert rows[0].position == 1
  assert rows[0].rank == '100.00%'
  assert rows[0].points == 26390291
  assert rows[0].history == ['1', '1', '1']

  # league_id is duplicate of league - excluded, not typed
  assert 'league_id' in rows[0].excluded()


def test_zpleague_team_event_results_parse_fixture():
  """Parse team-event standings rows from the real league-3379 fixture."""

  with open('test/fixtures/league_team_event_standings_3379.json', encoding='utf-8') as f:
    data = json.load(f)
  rows = [ZPLeagueTeamEventResult.from_dict(r) for r in data['data']]
  assert len(rows) == 20

  # Typed fields on the top row
  assert rows[0].position == 1
  assert rows[0].category == 'A'
  assert rows[0].zwift_id == 8325416
  assert rows[0].name == 'PedroJ. López (TEZH)'
  assert rows[0].team_id == 20380
  assert rows[0].team_name == 'TEZH Racing'
  assert rows[0].rank == '100.00%'

  # Recognized-but-untyped fields land in excluded
  assert 'topen' in rows[0].excluded()


def test_zpleague_info_parse_fixture():
  """Parse league metadata rows from the real league catalog fixture."""

  with open('test/fixtures/league_list.json', encoding='utf-8') as f:
    rows = json.load(f)['data']
  assert len(rows) == 3379


  row = next(r for r in rows if r['league_id'] == '3379')
  info = ZPLeagueInfo.from_dict(row)


  assert info.league_id == 3379
  assert info.name == ' #DURA-ACE | Standard'
  assert info.active == 1
  assert info.categories == 'A,B,C,D,E'
  assert info.races == 530
  assert info.efforts == 24994
  assert info.color_background == 'f95b0f'


  row2 = next(r for r in rows if r['league_id'] == '3388')
  info2 = ZPLeagueInfo.from_dict(row2)
  assert info2.name == 'Pain Cave Ultra'

  # Race display colors are recognized-but-untyped
  assert 'ridc' in info.excluded()


def test_zpleague_all_collections():
  """ZPLeague carries all five collections through asdict/accessors."""

  league = ZPLeague.from_dict(
    {
      'teams': {
        '1': {'tname': 'Team A', 'tbc': 'a', 'tbd': 'b', 'tc': 'c'},
      },
      'data': [
        {'pos': 1, 'zwid': 2, 'name': 'Rider One'},
      ],
    },
    league_id=2780,
    events=[{'zid': '10', 't': 'Event One', 'tm': 111}],
    team_standings=[
      {
        'tid': '9',
        'tname': 'SISU Racing',
        'pos': 1,
        'category': 'A',
        'rank': '100.00%',
        'points': '26390291',
      },
    ],
    team_event_results=[
      {
        'zwid': '8325416',
        'name': 'PedroJ. López (TEZH)',
        'tid': '20380',
        'tname': 'TEZH Racing',
        'pos': 1,
        'category': 'A',
      },
    ],
    league_info={
      'league_id': '2780',
      'league_name': ' #DURA-ACE | Standard',
      'cats': 'A,E',
      'races': '530',
      'efforts': '24994',
      'active': 1,
    },
  )

  d = league.asdict()
  assert d['league_id'] == 2780
  assert d['league_info']['name'] == ' #DURA-ACE | Standard'
  assert d['teams']['1']['name'] == 'Team A'
  assert d['standings'][0]['name'] == 'Rider One'
  assert d['team_standings'][0]['team_name'] == 'SISU Racing'
  assert d['team_event_results'][0]['team_name'] == 'TEZH Racing'
  assert d['events'][0]['event_id'] == 10

  # Accessors
  assert league.events()[0].event_id == 10
  assert league.team_standings()[0].points == 26390291
  assert league.team_event_results()[0].zwift_id == 8325416
  assert league.info().races == 530

  # Dict-style access
  assert league['events'][0].event_id == 10
  assert league['league_info'].name == ' #DURA-ACE | Standard'
  assert league['team_standings'][0].team_id == 9
  assert league['team_event_results'][0].team_id == 20380

  # json() output includes everything
  json_str = league.json()
  assert 'team_standings' in json_str
  assert 'team_event_results' in json_str
  assert 'events' in json_str
  assert 'league_info' in json_str


def test_zpleague_empty_collections_omitted():
  """Empty collections are omitted from asdict (existing contract)."""

  league = ZPLeague.from_dict({}, league_id=5)
  assert league.asdict() == {'league_id': 5}
  assert league.events() == []
  assert league.team_standings() == []
  assert league.team_event_results() == []
  assert league.info() is None


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


def _load_fixture(name):
  with open(f'test/fixtures/{name}', encoding='utf-8') as f:
    return json.load(f)


def _all_sources_handler(login_page, logged_in_page, league_ok):
  """Handler answering every league source with real fixture rows."""
  team_rows = _load_fixture('league_team_standings_3379.json')['data'][:3]
  tes_rows = _load_fixture('league_team_event_standings_3379.json')['data'][:3]
  event_rows = _load_fixture('league_event_results_3388.json')['data'][:5]
  catalog = _load_fixture('league_list.json')['data']
  catalog_row = next(r for r in catalog if r['league_id'] == '3379').copy()
  catalog_row['league_id'] = '2780'

  def handler(request):
    url = str(request.url)
    if request.method == 'GET' and 'login' in url:
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'league_team_standings_2780.json' in url:
      return httpx2.Response(200, text=json.dumps({'data': team_rows}))
    if 'league_team_event_standings' in url:
      return httpx2.Response(200, text=json.dumps({'data': tes_rows}))
    if 'league_event_results&id=2780' in url:
      return httpx2.Response(200, text=json.dumps({'data': event_rows}))
    if 'do=league_list' in url:
      return httpx2.Response(200, text=json.dumps({'data': [catalog_row]}))
    if 'league_standings_2780.json' in url:
      return httpx2.Response(200, text=json.dumps(league_ok))
    return httpx2.Response(404)

  return handler


def _async_client(handler):
  return httpx2.AsyncClient(
    follow_redirects=True,
    transport=httpx2.MockTransport(handler),
  )


@pytest.mark.anyio
async def test_league_afetch_all_sources(
  league_ok,
  login_page,
  logged_in_page,
):
  """Async fetch populates all five league collections."""
  handler = _all_sources_handler(login_page, logged_in_page, league_ok)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(_async_client(handler))

    league = ZPLeagueFetch()
    league.set_session(zp)

    result = await league.afetch(2780)

  obj = result[2780]
  assert obj.events()[0].title.startswith('Sykkelkomponenter')
  assert obj.team_standings()[0].team_name == 'SISU Racing'
  assert obj.team_event_results()[0].team_name == 'TEZH Racing'
  assert obj.info() is not None
  assert obj.info().name == ' #DURA-ACE | Standard'
  assert obj.standings()[0].name == 'Rider One'

  # asdict exposes everything
  d = obj.asdict()
  assert 'events' in d and 'team_standings' in d
  assert 'team_event_results' in d and 'league_info' in d


@pytest.mark.anyio
async def test_league_afetch_events_only_when_standings_fail(
  login_page,
  logged_in_page,
):
  """Standings 403 but events present -> league returned with events only."""
  events = _load_fixture('league_event_results_3388.json')['data']

  def handler(request):
    url = str(request.url)
    if request.method == 'GET' and 'login' in url:
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'league_event_results&id=3388' in url:
      return httpx2.Response(200, text=json.dumps({'data': events}))
    return httpx2.Response(403)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(_async_client(handler))

    league = ZPLeagueFetch()
    league.set_session(zp)

    result = await league.afetch(3388)

  obj = result[3388]
  assert len(obj.events()) == 12
  d = obj.asdict()
  assert 'events' in d
  assert 'standings' not in d
  assert 'team_standings' not in d


@pytest.mark.anyio
async def test_league_afetch_all_sources_fail(login_page, logged_in_page):
  """All per-league sources failing raises."""

  def handler(request):
    return httpx2.Response(403)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(_async_client(handler))

    league = ZPLeagueFetch()
    league.set_session(zp)

    with pytest.raises(Exception):
      await league.afetch(3388)


def test_league_fetch_sequential_all_sources(
  league_ok,
  login_page,
  logged_in_page,
):
  """Synchronous mode populates all five collections."""
  handler = _all_sources_handler(login_page, logged_in_page, league_ok)

  original_init = ZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx2.Client(
      follow_redirects=True,
      transport=httpx2.MockTransport(handler),
    )

  ZP.__init__ = mock_init
  ZPLeagueFetch.set_sync_mode(True)
  try:
    league = ZPLeagueFetch()
    result = league.fetch(2780)
  finally:
    ZPLeagueFetch.set_sync_mode(False)
    ZP.__init__ = original_init

  obj = result[2780]
  assert obj.events()
  assert obj.team_standings()
  assert obj.team_event_results()
  assert obj.info() is not None


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
