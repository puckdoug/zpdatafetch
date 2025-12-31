"""Conftest for shared module tests."""

import pytest
from keyrings.alt.file import PlaintextKeyring

from zpdatafetch import Config


@pytest.fixture
def config():
  """Fixture for Config with PlaintextKeyring."""
  config_instance = Config()
  config_instance.set_keyring(PlaintextKeyring())
  return config_instance
