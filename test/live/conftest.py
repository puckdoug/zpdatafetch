"""Shared fixtures for live API tests.

Live tests make real API calls and require valid credentials.
Run with: pytest --live
"""

import keyring
import pytest

from zpdatafetch import Config
from zrdatafetch.config import ZRConfig


def pytest_addoption(parser):
  """Add --live option to pytest."""
  parser.addoption(
    '--live',
    action='store_true',
    default=False,
    help='run live tests that make real API calls',
  )


def pytest_configure(config):
  """Register live marker."""
  config.addinivalue_line(
    'markers',
    'live: marks tests that make real API calls (requires --live flag)',
  )


def pytest_collection_modifyitems(config, items):
  """Skip live tests unless --live is passed."""
  if config.getoption('--live'):
    # --live given in cli: do not skip live tests
    return

  skip_live = pytest.mark.skip(reason='need --live option to run')
  for item in items:
    if 'live' in item.keywords:
      item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def use_real_credentials(request, setup_test_credentials):
  """Override test credentials to use real credentials for live tests.

  Depends on setup_test_credentials to ensure it runs after the root
  conftest sets up the test domain override.
  """
  # Only apply to live tests
  if 'live' not in request.keywords:
    return

  # Save current state set by setup_test_credentials
  zp_override = Config._test_domain_override
  zr_override = ZRConfig._test_domain_override
  saved_keyring = keyring.get_keyring()

  # Restore real system keyring and clear domain overrides for live tests
  # Use the system-specific backend (macOS Keychain on macOS)
  for backend in keyring.backend.get_all_keyring():
    if (
      'macOS' in type(backend).__module__ or 'SecretService' in type(backend).__module__
    ):
      keyring.set_keyring(backend)
      break
  Config._test_domain_override = None
  ZRConfig._test_domain_override = None

  yield

  # Restore test state after test
  Config._test_domain_override = zp_override
  ZRConfig._test_domain_override = zr_override
  keyring.set_keyring(saved_keyring)
