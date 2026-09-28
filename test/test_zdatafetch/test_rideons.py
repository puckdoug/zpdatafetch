"""Tests for Zwift RideOn data fetching."""

import json

import httpx2

from zdatafetch.rideons import ZwiftRideOns


def test_rideons_initialization():
  """Test ZwiftRideOns initialization."""
  rideons = ZwiftRideOns()

  assert rideons._raw == ''
  assert rideons._fetched == {}
  assert rideons.rider_id == 0
  assert rideons.activity_id == 0
  assert rideons.rideons == []


def test_parse_response():
  """Test parsing raw RideOn data."""
  rideons = ZwiftRideOns()
  rideons.rider_id = 550564
  rideons.activity_id = 12345678

  rideons._raw = json.dumps(
    [
      {'id': 123456, 'firstName': 'John', 'lastName': 'Doe'},
      {'id': 789012, 'firstName': 'Jane', 'lastName': 'Smith'},
    ],
  )

  rideons._parse_response()

  assert len(rideons.rideons) == 2
  assert rideons.rideons[0]['id'] == 123456
  assert rideons.rideons[1]['id'] == 789012


def test_rideon_count():
  """Test RideOn count helper."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    {'id': 1},
    {'id': 2},
    {'id': 3},
  ]

  assert rideons.rideon_count() == 3


def test_rideon_ids():
  """Test extracting rider IDs who gave RideOns."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    {'id': 123, 'firstName': 'John'},
    {'id': 456, 'firstName': 'Jane'},
  ]

  ids = rideons.rideon_ids()
  assert ids == [123, 456]


def test_has_rideon_from():
  """Test checking if specific rider gave RideOn."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    {'id': 123, 'firstName': 'John'},
    {'id': 456, 'firstName': 'Jane'},
  ]

  assert rideons.has_rideon_from(123) is True
  assert rideons.has_rideon_from(456) is True
  assert rideons.has_rideon_from(999) is False


def test_str_representation():
  """Test string representation."""
  rideons = ZwiftRideOns()
  rideons.rider_id = 550564
  rideons.activity_id = 12345678
  rideons.rideons = [{'id': 1}, {'id': 2}]
  rideons._fetched = {'rideons': rideons.rideons}

  output = str(rideons)
  assert 'ZwiftRideOns(rider_id=550564, activity_id=12345678)' in output
  assert 'rideons:' in output


def test_json_serialization():
  """Test JSON serialization."""
  rideons = ZwiftRideOns()
  rideons._fetched = {
    'rideons': [
      {'id': 123, 'firstName': 'John'},
      {'id': 456, 'firstName': 'Jane'},
    ],
  }

  json_str = rideons.json()
  data = json.loads(json_str)
  assert 'rideons' in data
  assert len(data['rideons']) == 2


def test_asdict():
  """Test dictionary access."""
  rideons = ZwiftRideOns()
  rideons._fetched = {'rideons': []}

  data = rideons.asdict()
  assert isinstance(data, dict)
  assert 'rideons' in data


def test_parse_empty_response():
  """Test parsing empty RideOn list."""
  rideons = ZwiftRideOns()
  rideons._raw = '[]'
  rideons._parse_response()

  assert rideons.rideons == []
  assert rideons.rideon_count() == 0


def test_parse_malformed_response():
  """Test parsing malformed response."""
  rideons = ZwiftRideOns()
  rideons._raw = '{"invalid": "not an array"}'
  rideons._parse_response()

  assert rideons.rideons == []
  assert rideons._fetched == {'rideons': []}


# give_rideon() tests (issue #9): the POST must carry a JSON payload
# with the authenticated caller's id, resolved via /api/profiles/me.


def _mock_http(monkeypatch, handler):
  """Swap httpx2.Client for a MockTransport(handler) client.

  Same mechanics as test_profile.py: patches the client used by
  zdatafetch.auth and zdatafetch.rideons, and replaces Config with a
  MockConfig so no keyring is touched. Returns a restore callable for
  use in try/finally.
  """
  import zdatafetch.auth
  import zdatafetch.rideons

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(handler))

  class MockConfig:
    username = 'test@example.com'
    password = 'testpassword'

    def load(self):
      pass

  zdatafetch.auth.httpx2.Client = mock_client
  zdatafetch.rideons.httpx2.Client = mock_client
  monkeypatch.setattr(zdatafetch.rideons, 'Config', MockConfig)

  def restore():
    zdatafetch.auth.httpx2.Client = original_client
    zdatafetch.rideons.httpx2.Client = original_client

  return restore


def _posts(recorder):
  """Return recorded POST requests from a give_rideon_handler."""
  return [c for c in recorder.calls if c['method'] == 'POST']


def test_give_rideon_sends_payload(give_rideon_handler, monkeypatch):
  """Regression: POST carries {'profileId': <caller id>} (issue #9).

  The mock returns 415 for a body-less or mistyped POST and 200 for a
  correct one, so this only passes when the payload is sent. URL path
  uses the activity owner id; payload uses the caller id.
  """
  restore = _mock_http(monkeypatch, give_rideon_handler)

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is True

    posts = _posts(give_rideon_handler)
    assert len(posts) == 1
    assert (
      '/api/profiles/550564/activities/12345678/rideon' in posts[0]['url']
    )
    assert 'application/json' in posts[0]['content_type']
    assert json.loads(posts[0]['body']) == {'profileId': 424242}
  finally:
    restore()


def test_give_rideon_resolves_me_before_post(
  give_rideon_handler,
  monkeypatch,
):
  """Caller id comes from GET /api/profiles/me, called before the POST.

  The mock answers 500 on the POST unless a /me GET was recorded
  first, so a passing run proves the lookup happened and that the
  payload reuses the id from the /me response.
  """
  restore = _mock_http(monkeypatch, give_rideon_handler)
  give_rideon_handler.state['require_me_before_post'] = True

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is True

    calls = give_rideon_handler.calls
    me_index = next(
      i for i, c in enumerate(calls) if c['url'].endswith('/api/profiles/me')
    )
    post_index = next(i for i, c in enumerate(calls) if c['method'] == 'POST')
    assert me_index < post_index
    assert json.loads(calls[post_index]['body']) == {'profileId': 424242}
  finally:
    restore()
