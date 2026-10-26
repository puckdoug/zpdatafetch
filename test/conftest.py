"""Root conftest.py - Global fixtures for all tests."""

import socket

import keyring
import pytest
from keyrings.alt.file import PlaintextKeyring

from zpdatafetch import Config
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import ZRConfig


def pytest_addoption(parser):
  """Add --live option to pytest."""
  parser.addoption(
    '--live',
    action='store_true',
    default=False,
    help='run live tests that make real API calls',
  )


def pytest_collection_modifyitems(config, items):
  """Skip live tests unless --live is passed."""
  if config.getoption('--live'):
    return

  skip_live = pytest.mark.skip(reason='need --live option to run')
  for item in items:
    if 'live' in item.keywords:
      item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def block_network_in_fast_tests(request, monkeypatch):
  """Fail non-live tests that attempt outbound network access."""
  if request.config.getoption('--live') and 'live' in request.keywords:
    yield
    return

  def blocked(*args, **kwargs):
    msg = (
      'Fast tests must not use the network. Mark the test with '
      '@pytest.mark.live and run with --live.'
    )
    raise RuntimeError(msg)

  monkeypatch.setattr(socket.socket, 'connect', blocked)
  monkeypatch.setattr(socket.socket, 'connect_ex', blocked)
  monkeypatch.setattr(socket, 'create_connection', blocked)
  monkeypatch.setattr(socket, 'getaddrinfo', blocked)
  yield


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


@pytest.fixture(autouse=True, scope='session')
def cleanup_shared_clients():
  """Clean up any shared HTTP clients after all tests complete."""
  yield
  # Clean up AsyncZR_obj shared client if it exists
  # We need to run this in an event loop, but we can't use async in a sync fixture
  # Instead, suppress the warning by clearing the client reference
  if AsyncZR_obj._shared_client:
    # Manually close without awaiting (best effort cleanup)
    try:
      import asyncio

      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      loop.run_until_complete(AsyncZR_obj.close_shared_session())
      loop.close()
    except Exception:
      # If we can't close properly, at least clear the reference to avoid the warning
      AsyncZR_obj._shared_client = None
