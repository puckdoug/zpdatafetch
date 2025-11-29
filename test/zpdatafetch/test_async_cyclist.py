"""Tests for Cyclist with async (afetch) methods."""

import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.cyclist import Cyclist


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

    cyclist = Cyclist()
    cyclist.set_session(zp)
    result = await cyclist.afetch(123456)

    assert 123456 in result
    assert result[123456] == test_data


@pytest.mark.anyio
async def test_async_cyclist_invalid_id():
  """Test AsyncCyclist rejects invalid IDs."""
  async with AsyncZP(skip_credential_check=True) as zp:
    cyclist = Cyclist()
    cyclist.set_session(zp)

    with pytest.raises(ValueError):
      await cyclist.afetch(0)  # Invalid: too small

    with pytest.raises(ValueError):
      await cyclist.afetch(-1)  # Invalid: negative

    with pytest.raises(ValueError):
      await cyclist.afetch(9999999999)  # Invalid: too large


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

    cyclist = Cyclist()
    cyclist.set_session(zp)
    result = await cyclist.afetch(123456, 789012)

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

    cyclist = Cyclist()
    cyclist.set_session(zp)
    await cyclist.afetch(123456)

    # Test json() method
    json_str = cyclist.json()
    assert '123456' in json_str

    # Test asdict() method
    data_dict = cyclist.asdict()
    assert 123456 in data_dict

    # Test __str__() method
    str_repr = str(cyclist)
    assert '123456' in str_repr
