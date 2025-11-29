import httpx

from zpdatafetch import Primes


def test_primes(primes):
  assert primes is not None


def test_primes_initialization(primes):
  assert primes.raw == {}


def test_primes_set_primetype():
  assert Primes.set_primetype('msec') == 'FAL'
  assert Primes.set_primetype('elapsed') == 'FTS'
  assert Primes.set_primetype('invalid') == ''


def test_primes_fetch(primes, login_page, logged_in_page):
  test_data = {'data': [{'position': 1, 'name': 'Prime Winner'}]}

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'event_primes' in str(request.url):
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
    result = primes.fetch(3590800)
    assert 3590800 in result
    # Should have categories A, B, C, D, E
    assert 'A' in result[3590800]
    # Each category should have msec and elapsed
    assert 'msec' in result[3590800]['A']
    assert 'elapsed' in result[3590800]['A']
  finally:
    ZP.__init__ = original_init
