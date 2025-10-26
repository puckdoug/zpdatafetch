"""Tests for async data classes (AsyncCyclist, AsyncResult, etc.)."""

import httpx
import pytest

from zpdatafetch.async_cyclist import AsyncCyclist
from zpdatafetch.async_primes import AsyncPrimes
from zpdatafetch.async_result import AsyncResult
from zpdatafetch.async_signup import AsyncSignup
from zpdatafetch.async_team import AsyncTeam
from zpdatafetch.async_zp import AsyncZP


@pytest.mark.anyio
async def test_async_cyclist_fetch(login_page, logged_in_page):
  """Test AsyncCyclist fetch functionality."""
  test_data = {'zwid': 123456, 'name': 'Test Cyclist'}

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if '123456' in str(request.url):
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

    cyclist = AsyncCyclist()
    cyclist.set_session(zp)
    result = await cyclist.fetch(123456)

    assert 123456 in result
    assert result[123456] == test_data


@pytest.mark.anyio
async def test_async_cyclist_invalid_id():
  """Test AsyncCyclist rejects invalid IDs."""
  async with AsyncZP(skip_credential_check=True) as zp:
    cyclist = AsyncCyclist()
    cyclist.set_session(zp)

    with pytest.raises(ValueError):
      await cyclist.fetch(0)  # Invalid: too small

    with pytest.raises(ValueError):
      await cyclist.fetch(-1)  # Invalid: negative

    with pytest.raises(ValueError):
      await cyclist.fetch(9999999999)  # Invalid: too large


@pytest.mark.anyio
async def test_async_result_fetch(login_page, logged_in_page):
  """Test AsyncResult fetch functionality."""
  test_data = {'race_id': 3590800, 'results': []}

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

    result = AsyncResult()
    result.set_session(zp)
    data = await result.fetch(3590800)

    assert 3590800 in data
    assert data[3590800] == test_data


@pytest.mark.anyio
async def test_async_signup_fetch(login_page, logged_in_page):
  """Test AsyncSignup fetch functionality."""
  test_data = {'race_id': 3590800, 'signups': []}

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

    signup = AsyncSignup()
    signup.set_session(zp)
    data = await signup.fetch(3590800)

    assert 3590800 in data
    assert data[3590800] == test_data


@pytest.mark.anyio
async def test_async_team_fetch(login_page, logged_in_page):
  """Test AsyncTeam fetch functionality."""
  test_data = {'team_id': 123, 'name': 'Test Team'}

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if '/123.' in str(request.url):
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

    team = AsyncTeam()
    team.set_session(zp)
    data = await team.fetch(123)

    assert 123 in data
    assert data[123] == test_data


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


@pytest.mark.anyio
async def test_async_multiple_fetches(login_page, logged_in_page):
  """Test fetching multiple IDs with async API."""

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if '123456' in str(request.url):
      return httpx.Response(200, json={'zwid': 123456})
    if '789012' in str(request.url):
      return httpx.Response(200, json={'zwid': 789012})
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

    cyclist = AsyncCyclist()
    cyclist.set_session(zp)
    result = await cyclist.fetch(123456, 789012)

    assert len(result) == 2
    assert 123456 in result
    assert 789012 in result


@pytest.mark.anyio
async def test_async_data_class_json_output(login_page, logged_in_page):
  """Test JSON serialization of async data classes."""
  test_data = {'zwid': 123456, 'name': 'Test'}

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if '123456' in str(request.url):
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

    cyclist = AsyncCyclist()
    cyclist.set_session(zp)
    await cyclist.fetch(123456)

    # Test json() method
    json_str = cyclist.json()
    assert '123456' in json_str

    # Test asdict() method
    data_dict = cyclist.asdict()
    assert 123456 in data_dict

    # Test __str__() method
    str_repr = str(cyclist)
    assert '123456' in str_repr
