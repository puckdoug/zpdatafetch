import json

import httpx


def test_team(team):
  assert team is not None


def test_team_initialization(team):
  assert team.raw == {}


def test_team_fetch_single_id(team, login_page, logged_in_page):
  test_data = {
    'data': [
      {'zwid': 123, 'name': 'Rider 1'},
      {'zwid': 456, 'name': 'Rider 2'},
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'teams' in str(request.url) and '.json' in str(request.url):
      return httpx.Response(200, text=json.dumps(test_data))
    return httpx.Response(404)

  from zpdatafetch.async_zp import AsyncZP

  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx.AsyncClient(
      follow_redirects=True,
      transport=httpx.MockTransport(handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    result = team.fetch(999)
    assert 999 in result
    assert result[999] == test_data
    assert len(result[999]['data']) == 2
  finally:
    AsyncZP.__init__ = original_init


def test_team_json_output(team):
  team.raw = {999: {'data': [{'name': 'Team Rider'}]}}
  json_str = team.json()
  assert '999' in json_str
  assert 'Team Rider' in json_str
