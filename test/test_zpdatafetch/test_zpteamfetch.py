import json

import httpx2

from zpdatafetch.zpteam import ZPTeam, ZPTeamMember


def test_zpteam_empty_instantiation():
  """Test that ZPTeam can be instantiated with no arguments."""
  obj = ZPTeam()
  assert obj is not None
  assert len(obj) == 0
  assert obj.aslist() == []


def test_zpteammember_empty_instantiation():
  """Test that ZPTeamMember can be instantiated with no arguments."""
  obj = ZPTeamMember()
  assert obj is not None
  assert obj.zwift_id == 0
  assert obj.name == ''


def test_zpteammember_from_dict_weight_with_thousands_separator():
  """Regression: ZwiftPower returns weight as a US-formatted string with a
  comma thousands separator for values >= 1000 (observed: '7,200.0' for team
  2707). ``ZPTeamMember.from_dict`` must parse this without raising."""
  member = ZPTeamMember.from_dict({'zwid': 1, 'w': '7,200.0'})
  assert member.weight == 7200.0


def test_team(team):
  assert team is not None


def test_team_initialization(team):
  assert team._raw == {}


def test_team_fetch_single_id(team, login_page, logged_in_page):
  from zpdatafetch.zpteam import ZPTeam

  test_data = {
    'data': [
      {'zwid': 123, 'name': 'Rider 1'},
      {'zwid': 456, 'name': 'Rider 2'},
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'teams' in str(request.url) and '.json' in str(request.url):
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
    result = team.fetch(999)
    assert 999 in result
    assert isinstance(result[999], ZPTeam)
    # Verify asdict() returns typed fields (not API format)
    asdict_result = result[999].asdict()
    assert 'data' in asdict_result
    assert len(asdict_result['data']) == 2
    # Verify data access through object interface
    assert len(result[999]) == 2
  finally:
    AsyncZP.__init__ = original_init


def test_team_json_output(team):
  from zpdatafetch.zpteam import ZPTeam

  team._fetched = {
    999: ZPTeam.from_dict({'data': [{'name': 'ZPTeamFetch Rider'}]})
  }
  json_str = team.json()
  assert '999' in json_str
  assert 'ZPTeamFetch Rider' in json_str
  assert 'ZPTeamFetch Rider' in json_str
