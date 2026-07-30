import json

import httpx2

from zpdatafetch.zpracesignup import ZPRaceSignup, ZPRiderSignup


def test_zpracesignup_empty_instantiation():
  """Test that ZPRaceSignup can be instantiated with no arguments."""
  obj = ZPRaceSignup()
  assert obj is not None
  assert len(obj) == 0
  assert obj.aslist() == []


def test_zpridersignup_empty_instantiation():
  """Test that ZPRiderSignup can be instantiated with no arguments."""
  obj = ZPRiderSignup()
  assert obj is not None
  assert obj.zwift_id == 0
  assert obj.name == ''
  assert obj.category == ''


def test_signup(signup):
  assert signup is not None


def test_signup_initialization(signup):
  assert signup._raw == {}


def test_signup_fetch_race_signups(signup, login_page, logged_in_page):
  test_data = {
    'data': [
      {'zwid': 123, 'name': 'Rider A', 'category': 'A'},
      {'zwid': 456, 'name': 'Rider B', 'category': 'B'},
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'results' in str(request.url) and '_signups.json' in str(request.url):
      return httpx2.Response(200, text=json.dumps(test_data))
    return httpx2.Response(404)

  from zpdatafetch.async_zp import AsyncZP

  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx2.AsyncClient(
      follow_redirects=True,
      transport=httpx2.MockTransport(handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    signup_result = signup.fetch(3590800)
    assert 3590800 in signup_result
    assert isinstance(signup_result[3590800], ZPRaceSignup)
    # Verify asdict() returns typed fields (not API format)
    asdict_result = signup_result[3590800].asdict()
    assert 'race_id' in asdict_result
    assert 'data' in asdict_result
    assert len(asdict_result['data']) == 2
    # Verify data access through object interface
    assert len(signup_result[3590800]) == 2
    assert signup_result[3590800][0].name == 'Rider A'
    assert signup_result[3590800][0].zwift_id == 123
    assert signup_result[3590800][1].name == 'Rider B'
    assert signup_result[3590800][1].zwift_id == 456
  finally:
    AsyncZP.__init__ = original_init
