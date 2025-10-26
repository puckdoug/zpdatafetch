import httpx

from zpdatafetch import Signup  # noqa: F401


def test_signup(signup):
  assert signup is not None


def test_signup_initialization(signup):
  assert signup.raw == {}


def test_signup_fetch_race_signups(signup, login_page, logged_in_page):
  test_data = {
    'data': [
      {'zwid': 123, 'name': 'Rider A', 'category': 'A'},
      {'zwid': 456, 'name': 'Rider B', 'category': 'B'},
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'results' in str(request.url) and '_signups.json' in str(request.url):
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
    signup_result = signup.fetch(3590800)
    assert 3590800 in signup_result
    assert signup_result[3590800] == test_data
  finally:
    ZP.__init__ = original_init
