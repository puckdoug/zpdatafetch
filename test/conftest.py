import pytest
from zp_data import ZP


@pytest.fixture
def zp():
  return ZP()
