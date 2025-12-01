"""Conftest for zrdatafetch module tests.

Provides fixtures for testing ZwiftRacing API responses.
"""

import json
from pathlib import Path

import pytest


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
