"""Conftest for zpdatafetch module tests."""

import json

import pytest

from zpdatafetch import ZP, Cyclist, League, Primes, Result, Signup, Sprints, Team


@pytest.fixture
def zp():
  """Fixture for ZP instance (skips credential check for testing)."""
  return ZP(skip_credential_check=True)


@pytest.fixture
def cyclist():
  """Fixture for Cyclist instance."""
  return Cyclist()


@pytest.fixture
def primes():
  """Fixture for Primes instance."""
  return Primes()


@pytest.fixture
def result():
  """Fixture for Result instance."""
  return Result()


@pytest.fixture
def signup():
  """Fixture for Signup instance."""
  return Signup()


@pytest.fixture
def sprints():
  """Fixture for Sprints instance."""
  return Sprints()


@pytest.fixture
def team():
  """Fixture for Team instance."""
  return Team()


@pytest.fixture
def league():
  """Fixture for League instance."""
  return League()


@pytest.fixture
def league_ok():
  """Test data for league endpoint."""
  return {'data': [{'div': 1, 'name': 'Rider One', 'team_name': 'Test Team'}]}


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
  import httpx

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'event_sprints' in str(request.url):
      return httpx.Response(200, text=json.dumps(sprints_test_data))
    if 'event_primes' in str(request.url):
      return httpx.Response(200, text=json.dumps({'data': []}))
    return httpx.Response(404)

  return handler
