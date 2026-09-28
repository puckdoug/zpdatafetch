"""Tests for Zwift RideOn data fetching."""

import json

import httpx2

from zdatafetch.rideons import ZwiftRideOns


def make_rideon(record_id, rider_id, first='John', last='Doe'):
  """Build a rideon record matching the verified production shape (gh#11)."""
  return {
    'id': record_id,
    'id_str': str(record_id),
    'activityId': 2236531212816564224,
    'activityId_str': '2236531212816564224',
    'profileId': rider_id,
    'fullName': f'{first} {last}',
    'profileImageUrl': f'https://static-cdn.zwift.com/prod/profile/{rider_id}',
    'profile': {
      'id': rider_id,
      'id_str': str(rider_id),
      'publicId': f'public-{rider_id}',
      'firstName': first,
      'lastName': last,
      'imageSrc': None,
      'imageSrcLarge': None,
      'countryCode': 756,
      'playerType': 'NORMAL',
      'socialFacts': {
        'followerStatusOfLoggedInPlayer': 'NO_RELATIONSHIP',
        'isFavoriteOfLoggedInPlayer': False,
      },
    },
    'createDate': '2026-09-20T10:00:00+00:00',
  }


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
      make_rideon(5597718940, 766087, first='John', last='Doe'),
      make_rideon(5597718941, 710061, first='Jane', last='Smith'),
    ],
  )

  rideons._parse_response()

  assert len(rideons.rideons) == 2
  assert rideons.rideons[0]['id'] == 5597718940
  assert rideons.rideons[0]['profile']['id'] == 766087
  assert rideons.rideons[1]['profile']['id'] == 710061


def test_rideon_count():
  """Test RideOn count helper."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    make_rideon(5597718940, 766087),
    make_rideon(5597718941, 710061),
    make_rideon(5597718942, 411292),
  ]

  assert rideons.rideon_count() == 3


def test_rideon_ids_extracts_rider_ids():
  """rideon_ids() must return rider IDs (profile.id), not record IDs (gh#11)."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    make_rideon(5597718940, 766087),
    make_rideon(5597718941, 710061),
  ]

  ids = rideons.rideon_ids()
  assert ids == [766087, 710061]
  # Regression essence: the rideon record IDs must NOT be returned.
  assert 5597718940 not in ids
  assert 5597718941 not in ids


def test_rideon_ids_skips_records_without_profile():
  """Records without a usable profile are skipped; result stays list[int]."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    make_rideon(5597718940, 766087),
    {'id': 1},  # no profile key
    {},  # empty record
    make_rideon(5597718941, 710061),
  ]

  ids = rideons.rideon_ids()
  assert ids == [766087, 710061]
  assert None not in ids


def test_rideon_ids_skips_bad_profile_values():
  """profile values that are unusable cause a skip, never a crash or None."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    make_rideon(5597718940, 766087),
    {'id': 2, 'profile': None},
    {'id': 3, 'profile': [1, 2]},
    {'id': 4, 'profile': {}},  # no id
    {'id': 5, 'profile': {'id': '123'}},  # non-int id
    make_rideon(5597718941, 710061),
  ]

  ids = rideons.rideon_ids()
  assert ids == [766087, 710061]
  assert None not in ids


def test_rideon_ids_skips_boolean_id():
  """bool must not enter list[int] (True is an int subclass)."""
  rideons = ZwiftRideOns()
  rideons.rideons = [
    make_rideon(5597718940, 766087),
    {'id': 6, 'profile': {'id': True}},
  ]

  assert rideons.rideon_ids() == [766087]


def test_has_rideon_from_real_shape():
  """has_rideon_from() matches rider IDs on real-shaped data (gh#11)."""
  rideons = ZwiftRideOns()
  rideons.rideons = [make_rideon(5597718940, 766087)]

  assert rideons.has_rideon_from(766087) is True
  # A rideon record ID must never match a rider lookup.
  assert rideons.has_rideon_from(5597718940) is False
  assert rideons.has_rideon_from(999) is False


def test_str_representation():
  """Test string representation."""
  rideons = ZwiftRideOns()
  rideons.rider_id = 550564
  rideons.activity_id = 12345678
  rideons.rideons = [
    make_rideon(5597718940, 766087),
    make_rideon(5597718941, 710061),
  ]
  rideons._fetched = {'rideons': rideons.rideons}

  output = str(rideons)
  assert 'ZwiftRideOns(rider_id=550564, activity_id=12345678)' in output
  assert 'rideons:' in output


def test_json_serialization():
  """Test JSON serialization."""
  rideons = ZwiftRideOns()
  rideons._fetched = {
    'rideons': [
      make_rideon(5597718940, 766087),
      make_rideon(5597718941, 710061),
    ],
  }

  json_str = rideons.json()
  data = json.loads(json_str)
  assert 'rideons' in data
  assert len(data['rideons']) == 2
  assert data['rideons'][0]['profile']['id'] == 766087


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
  """Return recorded rideon POSTs (excluding the auth token POST)."""
  return [
    c for c in recorder.calls
    if c['method'] == 'POST' and c['url'].endswith('/rideon')
  ]


def _me_gets(recorder):
  """Return recorded /api/profiles/me GETs from a give_rideon_handler."""
  return [
    c for c in recorder.calls if c['url'].endswith('/api/profiles/me')
  ]


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
    post_index = next(
      i for i, c in enumerate(calls)
      if c['method'] == 'POST' and c['url'].endswith('/rideon')
    )
    assert me_index < post_index
    assert json.loads(calls[post_index]['body']) == {'profileId': 424242}
  finally:
    restore()


def test_give_rideon_me_500_returns_false(
  give_rideon_handler,
  monkeypatch,
  caplog,
):
  """GET /me failing with 500: return False, never POST."""
  restore = _mock_http(monkeypatch, give_rideon_handler)
  give_rideon_handler.state['me_status'] = 500

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is False
    assert _posts(give_rideon_handler) == []
    assert 'Failed to resolve authenticated rider id' in caplog.text
  finally:
    restore()


def test_give_rideon_me_missing_id_returns_false(
  give_rideon_handler,
  monkeypatch,
  caplog,
):
  """GET /me response without an id: return False, never POST."""
  restore = _mock_http(monkeypatch, give_rideon_handler)
  give_rideon_handler.state['me_body'] = {'firstName': 'X'}

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is False
    assert _posts(give_rideon_handler) == []
    assert 'authenticated rider id' in caplog.text
  finally:
    restore()


def test_give_rideon_me_network_error_returns_false(
  give_rideon_handler,
  monkeypatch,
  caplog,
):
  """GET /me raising a network error: return False, never POST."""
  restore = _mock_http(monkeypatch, give_rideon_handler)
  give_rideon_handler.state['me_error'] = httpx2.ConnectError

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is False
    assert _posts(give_rideon_handler) == []
    assert 'Network error' in caplog.text
  finally:
    restore()


def test_give_rideon_post_404_returns_false(
  give_rideon_handler,
  monkeypatch,
  caplog,
):
  """POST answering 404: return False, error logged."""
  restore = _mock_http(monkeypatch, give_rideon_handler)
  give_rideon_handler.state['post_status'] = 404

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is False
    posts = _posts(give_rideon_handler)
    assert len(posts) == 1
    assert json.loads(posts[0]['body']) == {'profileId': 424242}
    assert 'not found for rider 550564' in caplog.text
  finally:
    restore()


def test_give_rideon_post_500_returns_false(
  give_rideon_handler,
  monkeypatch,
  caplog,
):
  """POST answering 500: return False, error logged."""
  restore = _mock_http(monkeypatch, give_rideon_handler)
  give_rideon_handler.state['post_status'] = 500

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is False
    posts = _posts(give_rideon_handler)
    assert len(posts) == 1
    assert json.loads(posts[0]['body']) == {'profileId': 424242}
    assert 'HTTP 500' in caplog.text
  finally:
    restore()


def test_give_rideon_timeout_returns_false(
  give_rideon_handler,
  monkeypatch,
  caplog,
):
  """POST timing out: return False, error logged."""
  restore = _mock_http(monkeypatch, give_rideon_handler)
  give_rideon_handler.state['post_error'] = httpx2.TimeoutException

  try:
    assert ZwiftRideOns.give_rideon(550564, 12345678) is False
    assert len(_me_gets(give_rideon_handler)) == 1
    assert 'timed out' in caplog.text
  finally:
    restore()
