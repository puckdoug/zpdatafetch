"""Tests for Primes with async (afetch) methods."""

import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.primes import Primes


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

    primes = Primes()
    primes.set_session(zp)
    data = await primes.afetch(3590800)

    assert 3590800 in data
    assert data[3590800] == test_data


@pytest.mark.anyio
async def test_async_primes_set_primetype():
  """Test Primes static primetype method."""
  assert Primes.set_primetype('sprint') == 'Sprint'
  assert Primes.set_primetype('kom') == 'KOM'
  assert Primes.set_primetype('prime') == 'Prime'
  assert Primes.set_primetype('unknown') == ''
