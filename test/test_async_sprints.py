"""Tests for Sprints with async (afetch) methods."""

import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.sprints import Sprints


@pytest.mark.anyio
async def test_async_sprints_fetch(login_page, logged_in_page):
  """Test AsyncSprints fetch functionality."""
  test_data = {
    'data': [
      {'sprint_id': 1, 'name': 'Sprint 1', 'distance': 500},
      {'sprint_id': 2, 'name': 'Sprint 2', 'distance': 750},
    ],
  }

  def handler(request):
    if request.method == 'GET' and 'login' in str(request.url):
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if '3590800' in str(request.url) and 'event_sprints' in str(request.url):
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

    sprints = Sprints()
    sprints.set_session(zp)
    data = await sprints.afetch(3590800)

    assert 3590800 in data
    assert data[3590800] == test_data
