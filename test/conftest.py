"""Root conftest.py - Global fixtures for all tests."""

import keyring
import pytest
from keyrings.alt.file import PlaintextKeyring

from zpdatafetch import Config


@pytest.fixture(scope='session', params=['asyncio', 'trio'])
def anyio_backend(request):
  """Configure pytest-anyio to test with both asyncio and trio backends."""
  return request.param


@pytest.fixture(autouse=True, scope='session')
def setup_test_credentials():
  """Automatically set up test credentials for all tests."""
  # Set the test domain override so all Config instances use it
  Config._test_domain_override = 'test-zpdatafetch-auto'

  # Set the keyring globally
  keyring.set_keyring(PlaintextKeyring())

  config = Config()
  config.setup(username='test_user', password='test_pass')
  yield
  # Cleanup after test
  Config._test_domain_override = None
