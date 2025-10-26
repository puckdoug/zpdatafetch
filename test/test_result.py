import httpx

from zpdatafetch import Result  # noqa: F401


def test_result(result):
  assert result is not None


def test_result_initialization(result):
  assert result.raw == {}


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
      return httpx.Response(200, json=test_data)
    return httpx.Response(404)

  from zpdatafetch.zp import ZP

  original_init = ZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self.init_client(
      httpx.Client(follow_redirects=True, transport=httpx.MockTransport(handler)),
    )

  ZP.__init__ = mock_init

  try:
    race_result = result.fetch(3590800)
    assert 3590800 in race_result
    assert race_result[3590800] == test_data
  finally:
    ZP.__init__ = original_init
