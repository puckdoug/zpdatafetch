import json

import httpx2

from zpdatafetch import ZPPrimesFetch
from zpdatafetch.zpprime import ZPPrime, ZPPrimeResult, ZPPrimeSegment


def test_zpprime_empty_instantiation():
  """Test that ZPPrime can be instantiated with no arguments."""
  obj = ZPPrime()
  assert obj is not None
  assert obj.asdict() == {'race_id': 0, '_categories': {}}
  assert len(obj.get_all_segments()) == 0


def test_zpprimesegment_empty_instantiation():
  """Test that ZPPrimeSegment can be instantiated with no arguments."""
  obj = ZPPrimeSegment()
  assert obj is not None
  result = obj.asdict()
  assert result == {
    'lap': 0,
    'name': '',
    'id': 0,
    'sprint_id': 0,
    'pen': '',
    '_results': [],
  }


def test_zpprimeresult_empty_instantiation():
  """Test that ZPPrimeResult can be instantiated with no arguments."""
  obj = ZPPrimeResult()
  assert obj is not None
  result = obj.asdict()
  assert result == {
    'zwift_id': 0,
    'name': '',
    'position': 0,
    'msec': 0,
    'finish_timestamp': '',
    'msec_diff': 0.0,
    'elapsed': 0.0,
    'elapsed_diff': 0.0,
    'zftp': 0,
    'weight': 0.0,
    'age': '',
    'gender': '',
    'flag': '',
    'rank': '',
    'skill': 0,
    'category': '',
  }


def test_primes(primes):
  assert primes is not None


def test_primes_initialization(primes):
  assert primes._raw == {}


def test_primes_set_primetype():
  assert ZPPrimesFetch.set_primetype('msec') == 'FAL'
  assert ZPPrimesFetch.set_primetype('elapsed') == 'FTS'
  assert ZPPrimesFetch.set_primetype('invalid') == ''


def test_primes_fetch(primes, login_page, logged_in_page):
  from zpdatafetch.zpprime import ZPPrime

  test_data = {'data': [{'position': 1, 'name': 'Prime Winner'}]}

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'event_primes' in str(request.url):
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
    result = primes.fetch(3590800)
    assert 3590800 in result
    assert isinstance(result[3590800], ZPPrime)
    # Should have categories A, B, C, D, E (via dict-style access)
    assert 'A' in result[3590800]
    # Each category should have msec and elapsed
    assert 'msec' in result[3590800]['A']
    assert 'elapsed' in result[3590800]['A']
  finally:
    AsyncZP.__init__ = original_init
