import keyring
import pytest
from keyrings.alt.file import PlaintextKeyring

from zpdatafetch import ZP, Config, Cyclist, Primes, Result, Signup, Sprints, Team


@pytest.fixture(scope='session', params=['asyncio', 'trio'])
def anyio_backend(request):
  """Configure pytest-anyio to test with both asyncio and trio backends"""
  return request.param


@pytest.fixture(autouse=True, scope='session')
def setup_test_credentials():
  """Automatically set up test credentials for all tests"""
  # Set the test domain override so all Config instances use it
  Config._test_domain_override = 'test-zpdatafetch-auto'

  # Set the keyring globally
  keyring.set_keyring(PlaintextKeyring())

  config = Config()
  config.setup(username='test_user', password='test_pass')
  yield
  # Cleanup after test
  Config._test_domain_override = None


@pytest.fixture
def zp():
  # Skip credential check for tests since we mock the client anyway
  return ZP(skip_credential_check=True)


@pytest.fixture
def cyclist():
  return Cyclist()


@pytest.fixture
def primes():
  return Primes()


@pytest.fixture
def result():
  return Result()


@pytest.fixture
def config():
  config_instance = Config()
  config_instance.set_keyring(PlaintextKeyring())
  return config_instance


@pytest.fixture
def signup():
  return Signup()


@pytest.fixture
def sprints():
  return Sprints()


@pytest.fixture
def team():
  return Team()


@pytest.fixture
def login_page():
  return open('test/fixtures/login_page.html', encoding='utf8').read()


@pytest.fixture
def logged_in_page():
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
      return httpx.Response(200, json=sprints_test_data)
    if 'event_primes' in str(request.url):
      return httpx.Response(200, json={'data': []})
    return httpx.Response(404)

  return handler
