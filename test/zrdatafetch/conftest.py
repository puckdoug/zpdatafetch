"""Conftest for zrdatafetch module tests.

Provides fixtures for testing ZwiftRacing API responses.
"""

import json
from pathlib import Path

import pytest

from zrdatafetch.config import ZRConfig


@pytest.fixture(autouse=True)
def clear_domain_override_for_config_tests(request):
  """Clear test domain override for config tests that check default domain.

  The root conftest sets a test domain override for all tests, but config
  tests need to verify the actual default domain behavior.
  """
  # Only clear for tests in test_config_zr.py
  if 'test_config_zr' in request.node.nodeid:
    saved_override = ZRConfig._test_domain_override
    ZRConfig._test_domain_override = None
    yield
    ZRConfig._test_domain_override = saved_override
  else:
    yield


@pytest.fixture
def zr_race_result_fixture():
  """Load real ZwiftRacing race result response for race ID 4613373.

  This fixture provides actual API response data from the
  /public/results/{race_id} endpoint, useful for testing parsing logic.

  Returns:
    str: Raw JSON string response containing race metadata and results array
  """
  fixture_path = (
    Path(__file__).parent.parent / 'fixtures' / 'zr_race_result_4613373.json'
  )
  with open(fixture_path, encoding='utf-8') as f:
    return f.read()
