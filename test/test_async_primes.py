"""Tests for AsyncPrimes."""

import httpx
import pytest

from zpdatafetch.async_primes import AsyncPrimes
from zpdatafetch.async_zp import AsyncZP


@pytest.mark.anyio
async def test_async_primes_fetch(login_page, logged_in_page):
  """Test AsyncPrimes fetch functionality."""
  test_data = {'race_id': 3590800, 'primes': []}

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if '3590800' in str(request.url):
      return httpx.Response(200, json=test_data)
    return httpx.Response(404)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )

    primes = AsyncPrimes()
    primes.set_session(zp)
    data = await primes.fetch(3590800)

    assert 3590800 in data
    assert data[3590800] == test_data


@pytest.mark.anyio
async def test_async_primes_set_primetype():
  """Test AsyncPrimes static primetype method."""
  assert AsyncPrimes.set_primetype('sprint') == 'Sprint'
  assert AsyncPrimes.set_primetype('kom') == 'KOM'
  assert AsyncPrimes.set_primetype('prime') == 'Prime'
  assert AsyncPrimes.set_primetype('unknown') == 'unknown'
