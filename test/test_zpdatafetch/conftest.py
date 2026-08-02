"""Conftest for zpdatafetch module tests."""

import json

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


@pytest.fixture
def zp():
  """Fixture for ZP instance (skips credential check for testing)."""
  return ZP(skip_credential_check=True)


@pytest.fixture
def cyclist():
  """Fixture for ZPCyclistFetch instance."""
  return ZPCyclistFetch()


@pytest.fixture
def primes():
  """Fixture for ZPPrimesFetch instance."""
  return ZPPrimesFetch()


@pytest.fixture
def result():
  """Fixture for ZPResultFetch instance."""
  return ZPResultFetch()


@pytest.fixture
def signup():
  """Fixture for ZPSignupFetch instance."""
  return ZPSignupFetch()


@pytest.fixture
def sprints():
  """Fixture for ZPSprintsFetch instance."""
  return ZPSprintsFetch()


@pytest.fixture
def team():
  """Fixture for ZPTeamFetch instance."""
  return ZPTeamFetch()


@pytest.fixture
def league():
  """Fixture for ZPLeagueFetch instance."""
  return ZPLeagueFetch()


@pytest.fixture
def league_ok():
  """Test data for league endpoint."""
  return {
    'teams': {
      '1': {
        'tname': 'Test Team',
        'tbc': 'ffffff',
        'tbd': '000000',
        'tc': 'ffffff',
      },
    },
    'data': [
      {
        'pos': 1,
        'zwid': 123456,
        'aid': 123456,
        'name': 'Rider One',
        'points': 100,
        'events': 5,
        'category': 'A',
        'tid': 1,
        'age': '30-39',
        'flag': 'us',
        'history': ['1', '2', '1', '1', '2'],
      },
    ],
  }


@pytest.fixture
def login_page():
  """Fixture for login page HTML."""
  return open('test/fixtures/login_page.html', encoding='utf8').read()


@pytest.fixture
def logged_in_page():
  """Fixture for logged in page HTML."""
  return open('test/fixtures/logged_in_page.html', encoding='utf8').read()


@pytest.fixture
def sprints_test_data():
  """Test data for sprints endpoint."""
  return {
    'data': [
      {'sprint_id': 1, 'name': 'Sprint 1', 'distance': 500},
      {'sprint_id': 2, 'name': 'Sprint 2', 'distance': 750},
    ],
  }


@pytest.fixture
def primes_test_data():
  """Test data for primes endpoint."""
  return {
    3590800: {
      'A': {
        'msec': {
          'data': [
            {'sprint_id': 1, 'name': 'Sprint 1'},
            {'sprint_id': 2, 'name': 'Sprint 2'},
          ],
        },
        'elapsed': {'data': []},
      },
    },
  }


@pytest.fixture
def sprints_handler(login_page, logged_in_page, sprints_test_data):
  """HTTP handler for sprints-related requests."""
  import httpx2

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'event_sprints' in str(request.url):
      return httpx2.Response(200, text=json.dumps(sprints_test_data))
    if 'event_primes' in str(request.url):
      return httpx2.Response(200, text=json.dumps({'data': []}))
    return httpx2.Response(404)

  return handler
