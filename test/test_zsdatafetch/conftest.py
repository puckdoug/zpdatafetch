"""Shared fixtures for zsdatafetch tests."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'zs'


@pytest.fixture
def summary_data():
  with open(FIXTURES_DIR / 'summary.json') as f:
    return json.load(f)


@pytest.fixture
def components_data():
  with open(FIXTURES_DIR / 'components.json') as f:
    return json.load(f)


@pytest.fixture
def incidents_data():
  with open(FIXTURES_DIR / 'incidents.json') as f:
    return json.load(f)


@pytest.fixture
def incidents_unresolved_data():
  with open(FIXTURES_DIR / 'incidents_unresolved.json') as f:
    return json.load(f)


@pytest.fixture
def maintenance_data():
  with open(FIXTURES_DIR / 'maintenance.json') as f:
    return json.load(f)


@pytest.fixture
def maintenance_upcoming_data():
  with open(FIXTURES_DIR / 'maintenance_upcoming.json') as f:
    return json.load(f)


@pytest.fixture
def maintenance_active_data():
  with open(FIXTURES_DIR / 'maintenance_active.json') as f:
    return json.load(f)


@pytest.fixture
def summary_json():
  with open(FIXTURES_DIR / 'summary.json') as f:
    return f.read()


@pytest.fixture
def components_json():
  with open(FIXTURES_DIR / 'components.json') as f:
    return f.read()


@pytest.fixture
def incidents_json():
  with open(FIXTURES_DIR / 'incidents.json') as f:
    return f.read()


@pytest.fixture
def incidents_unresolved_json():
  with open(FIXTURES_DIR / 'incidents_unresolved.json') as f:
    return f.read()


@pytest.fixture
def maintenance_json():
  with open(FIXTURES_DIR / 'maintenance.json') as f:
    return f.read()


@pytest.fixture
def maintenance_upcoming_json():
  with open(FIXTURES_DIR / 'maintenance_upcoming.json') as f:
    return f.read()


@pytest.fixture
def maintenance_active_json():
  with open(FIXTURES_DIR / 'maintenance_active.json') as f:
    return f.read()
