"""Root conftest.py - Global fixtures for all tests."""

import keyring
import pytest
from keyrings.alt.file import PlaintextKeyring

from zpdatafetch import Config
from zrdatafetch.config import ZRConfig


@pytest.fixture(scope='session', params=['asyncio', 'trio'])
def anyio_backend(request):
  """Configure pytest-anyio to test with both asyncio and trio backends."""
  return request.param


@pytest.fixture(autouse=True, scope='session')
def setup_test_credentials():
  """Automatically set up test credentials for all tests."""
  # Set the test domain override so all Config instances use it
  Config._test_domain_override = 'test-zpdatafetch-auto'
  ZRConfig._test_domain_override = 'test-zrdatafetch-auto'

  # Set the keyring globally
  keyring.set_keyring(PlaintextKeyring())

  # Set up ZP credentials
  config = Config()
  config.setup(username='test_user', password='test_pass')

  # Set up ZR credentials
  zr_config = ZRConfig()
  zr_config.setup(authorization='test_auth_token')

  yield
  # Cleanup after test
  Config._test_domain_override = None
  ZRConfig._test_domain_override = None
