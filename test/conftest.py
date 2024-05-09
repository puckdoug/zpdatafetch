import pytest
from zp_data.zp import ZP


@pytest.fixture
def zp():
  return ZP()
