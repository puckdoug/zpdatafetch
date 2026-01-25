import json

import httpx

from zpdatafetch.zpraceresult import ZPRaceResult, ZPRiderFinish


def test_zpraceresult_empty_instantiation():
  """Test that ZPRaceResult can be instantiated with no arguments."""
  obj = ZPRaceResult()
  assert obj is not None
  assert len(obj) == 0
  assert obj.aslist() == []


def test_zpriderfinish_empty_instantiation():
  """Test that ZPRiderFinish can be instantiated with no arguments."""
  obj = ZPRiderFinish()
  assert obj is not None
  # Dataclass default: all fields populated with type defaults
  result = obj.asdict()
  assert result['position'] == 0
  assert result['name'] == ''
  assert result['zwift_id'] == 0


def test_result(result):
  assert result is not None


def test_result_initialization(result):
  assert result._raw == {}


def test_result_fetch_race_results(result, login_page, logged_in_page):
  test_data = {
    'data': [
      {'position': 1, 'name': 'Winner', 'time': '01:23:45'},
      {'position': 2, 'name': 'Second Place', 'time': '01:24:12'},
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'results' in str(request.url) and '_view.json' in str(request.url):
      return httpx.Response(200, text=json.dumps(test_data))
    return httpx.Response(404)

  from zpdatafetch.async_zp import AsyncZP

  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx.AsyncClient(
      follow_redirects=True,
      transport=httpx.MockTransport(handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    race_result = result.fetch(3590800)
    assert 3590800 in race_result
    assert isinstance(race_result[3590800], ZPRaceResult)
    # Verify structure: should have data array with riders
    result_dict = race_result[3590800].asdict()
    assert 'data' in result_dict
    assert len(race_result[3590800]) == 2
    assert race_result[3590800][0]['name'] == 'Winner'
    # Verify rider data is preserved
    assert result_dict['data'][0]['position'] == 1
    assert result_dict['data'][0]['name'] == 'Winner'
  finally:
    AsyncZP.__init__ = original_init
