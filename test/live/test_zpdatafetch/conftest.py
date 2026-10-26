"""Fixtures for zpdatafetch live tests.

Live tests share one authenticated session. ZwiftPower blocks rapid repeat
logins, so creating a new session in every test makes the suite unreliable.
Tests are also spaced out to stay clear of ZwiftPower rate limits.
"""

import json
import time

import pytest

from zpdatafetch import (
  ZP,
  ZPCyclistFetch,
  ZPLeagueFetch,
  ZPPrimesFetch,
  ZPResultFetch,
  ZPSignupFetch,
  ZPSprintsFetch,
  ZPTeamFetch,
)

_FETCH_CLASSES = (
  ZPCyclistFetch,
  ZPLeagueFetch,
  ZPPrimesFetch,
  ZPResultFetch,
  ZPSignupFetch,
  ZPSprintsFetch,
  ZPTeamFetch,
)

_LIVE_TEST_INTERVAL = 10.0
_last_live_test = 0.0


@pytest.fixture
def valid_zwift_id():
  """Single valid Zwift ID for testing."""
  return 486314


@pytest.fixture
def valid_zwift_ids():
  """Multiple valid Zwift IDs for testing."""
  return [486314, 2417653]


@pytest.fixture
def valid_event_id():
  """Single valid event ID for testing."""
  return 5240126


@pytest.fixture
def valid_event_ids():
  """Multiple valid event IDs for testing."""
  return [5240126, 5240100]


@pytest.fixture
def valid_team_id():
  """Single valid team ID for testing."""
  return 21663


@pytest.fixture
def valid_league_id():
  """Single valid league ID for testing."""
  return 1990


@pytest.fixture
def valid_league_ids():
  """Multiple valid league IDs for testing."""
  return [1990, 2678, 3017]


@pytest.fixture(scope='session')
def _live_zp_holder():
  """Hold the shared session and close it after the run."""
  holder: dict[str, ZP] = {}
  yield holder
  if 'zp' in holder:
    holder['zp'].close()


@pytest.fixture
def live_zp(_live_zp_holder, use_real_credentials):
  """Return one authenticated ZP session for all live ZP tests."""
  if 'zp' not in _live_zp_holder:
    zp = ZP()
    zp.login()
    _live_zp_holder['zp'] = zp
  return _live_zp_holder['zp']


@pytest.fixture(autouse=True)
def space_live_zp_tests(request):
  """Wait between live ZwiftPower tests to avoid rate limiting."""
  if 'live' not in request.keywords:
    yield
    return

  global _last_live_test

  if _last_live_test:
    wait = _LIVE_TEST_INTERVAL - (time.monotonic() - _last_live_test)
    if wait > 0:
      time.sleep(wait)

  yield

  _last_live_test = time.monotonic()


@pytest.fixture(autouse=True)
def use_shared_zp_session(request, live_zp, monkeypatch):
  """Make live fetchers reuse the shared authenticated ZP session."""
  if 'live' not in request.keywords:
    yield
    return

  for cls in _FETCH_CLASSES:
    original_init = cls.__init__

    def init(self, *args, __original=original_init, **kwargs):
      __original(self, *args, **kwargs)
      self.set_zp_session(live_zp)

    monkeypatch.setattr(cls, '__init__', init)
  yield


@pytest.fixture
def league_fixtures():
  """Load league fixture data from test/fixtures/ directory.

  The fixture files contain the processed format: {"id": {data}}
  We extract the data dict for each ID.
  """
  fixtures = {}
  for league_id in [1990, 2678, 3017]:
    with open(f'test/fixtures/league_{league_id}.json', encoding='utf8') as f:
      data = json.load(f)
      # data is {"1990": {...}} - extract the value for the string key
      fixtures[league_id] = data[str(league_id)]
  return fixtures
