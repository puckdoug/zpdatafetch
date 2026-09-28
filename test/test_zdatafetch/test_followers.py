"""Tests for Zwift followers/followees data fetching."""

import json
import logging

import httpx2
import pytest

from shared.exceptions import NetworkError
from zdatafetch import followers as followers_mod
from zdatafetch.followers import ZwiftFollowers

OWNER_ID = 550564

TOKEN_RESPONSE = {
  'access_token': 'mock_access_token_12345',
  'token_type': 'Bearer',
  'expires_in': 3600,
  'refresh_token': 'mock_refresh_token_67890',
  'refresh_expires_in': 7200,
}


def make_relation(rider_id, relation_id, role='follower'):
  """Build a follower/followee record in the documented API shape."""
  profile = {
    'id': rider_id,
    'id_str': str(rider_id),
    'publicId': f'public-{rider_id}',
    'firstName': 'John',
    'lastName': 'Doe',
    'male': True,
    'imageSrc': None,
    'imageSrcLarge': None,
    'playerType': 'NORMAL',
    'countryAlpha3': 'che',
    'countryCode': 756,
    'useMetric': True,
    'riding': False,
    'privacy': {
      'approvalRequired': False,
      'displayWeight': False,
      'minor': False,
      'privateMessaging': False,
      'defaultFitnessDataPrivacy': False,
      'suppressFollowerNotification': False,
      'displayAge': True,
      'defaultActivityPrivacy': 'PUBLIC',
    },
    'socialFacts': {
      'profileId': rider_id,
      'followersCount': 10,
      'followeesCount': 5,
      'followeesInCommonWithLoggedInPlayer': 0,
      'followerStatusOfLoggedInPlayer': 'NO_RELATIONSHIP',
      'followeeStatusOfLoggedInPlayer': 'NO_RELATIONSHIP',
      'isFavoriteOfLoggedInPlayer': False,
    },
    'worldId': None,
    'enrolledZwiftAcademy': False,
    'playerTypeId': 1,
    'playerSubTypeId': None,
    'currentActivityId': None,
  }
  return {
    'id': relation_id,
    'followerId': rider_id if role == 'follower' else OWNER_ID,
    'followeeId': OWNER_ID if role == 'follower' else rider_id,
    'status': 'IS_FOLLOWING',
    'isFolloweeFavoriteOfFollower': False,
    'followerProfile': profile if role == 'follower' else None,
    'followeeProfile': profile if role == 'followee' else None,
  }


def make_page(start_rel, count, role='follower'):
  """Build one page of records with unique rider/relation IDs."""
  return [
    make_relation(100000 + start_rel + i, 9000000000 + start_rel + i, role)
    for i in range(count)
  ]


class PageSource:
  """In-memory paginated endpoints served through MockTransport.

  Pages map (rider_id, endpoint, start) to a list of records, an HTTP
  status int to force a failure, or a str to serve as raw body. Every
  request is recorded as (rider_id, endpoint, start, limit).
  """

  def __init__(self) -> None:
    self.pages = {}
    self.requests = []

  def add(self, rider_id, endpoint, start, page):
    self.pages[(rider_id, endpoint, start)] = page

  def handler(self, request):
    if 'access/codes' in str(request.url):
      return httpx2.Response(200, text=json.dumps(TOKEN_RESPONSE))
    parts = str(request.url).split('?')[0].split('/')
    rider_id = int(parts[-2])
    endpoint = parts[-1]
    start = int(request.url.params.get('start', 0))
    limit = int(request.url.params.get('limit', 0))
    self.requests.append((rider_id, endpoint, start, limit))
    page = self.pages.get((rider_id, endpoint, start))
    if page is None:
      return httpx2.Response(404, text='Not found')
    if isinstance(page, str):
      return httpx2.Response(200, text=page)
    if isinstance(page, int):
      return httpx2.Response(page, text='error')
    return httpx2.Response(200, text=json.dumps(page))


def patch_fetch(source, monkeypatch):
  """Patch auth, config, and HTTP client to serve source's pages."""
  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(source.handler))

  zdatafetch.auth.httpx2.Client = mock_client
  followers_mod.httpx2.Client = mock_client

  class MockConfig:
    username = 'test@example.com'
    password = 'testpassword'

    def load(self):
      pass

  monkeypatch.setattr(followers_mod, 'Config', MockConfig)
  return original_client


def restore_clients(original_client):
  """Restore the real httpx2.Client after a test."""
  import zdatafetch.auth

  zdatafetch.auth.httpx2.Client = original_client
  followers_mod.httpx2.Client = original_client


def expose_warnings(caplog, monkeypatch):
  """Route zdatafetch log records into caplog for warning assertions."""
  caplog.set_level(logging.WARNING, logger='zdatafetch.followers')
  monkeypatch.setattr(logging.getLogger('zdatafetch'), 'propagate', True)
  monkeypatch.setattr(
    logging.getLogger('zdatafetch.followers'), 'propagate', True,
  )


def follower_requests(source, rider_id=None):
  """Return recorded (start, limit) tuples for a rider's followers calls."""
  return [
    (r[2], r[3]) for r in source.requests
    if r[1] == 'followers' and (rider_id is None or r[0] == rider_id)
  ]


def test_followers_initialization():
  """Test ZwiftFollowers initialization."""
  followers = ZwiftFollowers()

  assert followers._raw == ''
  assert followers._fetched == {}
  assert followers.rider_id == 0
  assert followers.followers == []
  assert followers.followees == []


def test_parse_response():
  """Test parsing raw follower data in the documented relation shape."""
  followers = ZwiftFollowers()
  followers.rider_id = OWNER_ID

  raw_data = {
    'followers': json.dumps(make_page(0, 2)),
    'followees': json.dumps(make_page(0, 1, role='followee')),
  }

  followers._parse_response(raw_data)

  assert len(followers.followers) == 2
  assert len(followers.followees) == 1
  assert followers.followers[0]['id'] == 9000000000
  assert followers.followers[0]['followerProfile']['id'] == 100000
  assert followers.followees[0]['followeeProfile']['id'] == 100000


def test_follower_count():
  """Test follower count helper."""
  followers = ZwiftFollowers()
  followers.followers = [
    make_relation(100001, 1),
    make_relation(100002, 2),
    make_relation(100003, 3),
  ]

  assert followers.follower_count() == 3


def test_followee_count():
  """Test followee count helper."""
  followers = ZwiftFollowers()
  followers.followees = [
    make_relation(100001, 1, role='followee'),
    make_relation(100002, 2, role='followee'),
  ]

  assert followers.followee_count() == 2


def test_follower_ids():
  """Test extracting follower IDs (relation row IDs; extraction bug is
  gh#11-class, out of scope here)."""
  followers = ZwiftFollowers()
  followers.followers = [
    make_relation(100001, 9000000001),
    make_relation(100002, 9000000002),
  ]

  ids = followers.follower_ids()
  assert ids == [9000000001, 9000000002]


def test_followee_ids():
  """Test extracting followee IDs (relation row IDs; out of scope)."""
  followers = ZwiftFollowers()
  followers.followees = [
    make_relation(100001, 9000000001, role='followee'),
    make_relation(100002, 9000000002, role='followee'),
  ]

  ids = followers.followee_ids()
  assert ids == [9000000001, 9000000002]


def test_mutual_followers():
  """Test finding mutual followers."""
  followers = ZwiftFollowers()
  followers.followers = [
    make_relation(100001, 1),
    make_relation(100002, 2),
    make_relation(100003, 3),
  ]
  followers.followees = [
    make_relation(100001, 1, role='followee'),  # Mutual
    make_relation(100009, 9, role='followee'),
  ]

  mutual = followers.mutual_followers()
  assert len(mutual) == 1
  assert mutual[0]['id'] == 1


def test_str_representation():
  """Test string representation."""
  followers = ZwiftFollowers()
  followers.rider_id = 550564
  followers.followers = [{'id': 1}, {'id': 2}]
  followers.followees = [{'id': 3}]
  followers._fetched = {
    'followers': followers.followers,
    'followees': followers.followees,
  }

  output = str(followers)
  assert 'ZwiftFollowers(rider_id=550564)' in output
  assert 'followers:' in output
  assert 'followees:' in output


def test_json_serialization():
  """Test JSON serialization."""
  followers = ZwiftFollowers()
  followers._fetched = {
    'followers': [{'id': 123}],
    'followees': [{'id': 456}],
  }

  json_str = followers.json()
  data = json.loads(json_str)
  assert 'followers' in data
  assert 'followees' in data
  assert len(data['followers']) == 1
  assert len(data['followees']) == 1


def test_asdict():
  """Test dictionary access."""
  followers = ZwiftFollowers()
  followers._fetched = {'followers': [], 'followees': []}

  data = followers.asdict()
  assert isinstance(data, dict)
  assert 'followers' in data
  assert 'followees' in data


def test_fetch_single_short_page(monkeypatch):
  """A page shorter than the limit fetches once and stores counts."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 3))
  source.add(OWNER_ID, 'followees', 0, make_page(0, 0))

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID)

    assert len(follower_requests(source)) == 1
    assert obj.follower_count() == 3
    assert obj.followee_count() == 0
    assert set(obj.fetched().keys()) == {'followers', 'followees'}
  finally:
    restore_clients(original_client)


def test_fetch_paginates_and_merges_in_order(monkeypatch):
  """250 followers across two pages merge in request order."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 200))
  source.add(OWNER_ID, 'followers', 200, make_page(200, 50))

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID)

    assert len(follower_requests(source)) == 2
    assert obj.follower_count() == 250
    assert obj.followers[0]['id'] == 9000000000
    assert obj.followers[-1]['id'] == 9000000249
    assert set(obj.fetched().keys()) == {'followers', 'followees'}
  finally:
    restore_clients(original_client)


def test_fetch_exact_full_pages_stop_on_empty(monkeypatch):
  """Exactly N x limit entries terminate via the empty-page condition."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 200))
  source.add(OWNER_ID, 'followers', 200, make_page(200, 200))
  source.add(OWNER_ID, 'followers', 400, make_page(400, 0))

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID, include_followees=False)

    assert len(follower_requests(source)) == 3
    assert obj.follower_count() == 400
  finally:
    restore_clients(original_client)


def test_fetch_sends_start_limit_params(monkeypatch):
  """Requests carry limit=200 and stepping start offsets."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 200))
  source.add(OWNER_ID, 'followers', 200, make_page(200, 50))

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID, include_followees=False)

    calls = follower_requests(source)
    assert all(limit == 200 for _, limit in calls)
    assert [start for start, _ in calls] == [0, 200]
  finally:
    restore_clients(original_client)


def test_fetch_followers_mid_pagination_failure_raises(monkeypatch):
  """A failed followers page mid-pagination raises NetworkError."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 200))
  source.add(OWNER_ID, 'followers', 200, 500)

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    with pytest.raises(
      NetworkError, match='Failed to fetch followers for rider 550564',
    ):
      obj.fetch(OWNER_ID)

    assert len(follower_requests(source)) == 2
  finally:
    restore_clients(original_client)


def test_fetch_followers_404_rider_not_found(monkeypatch):
  """A followers 404 raises the 'Rider not found' NetworkError."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, 404)

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    with pytest.raises(NetworkError, match='Rider 550564 not found'):
      obj.fetch(OWNER_ID)
  finally:
    restore_clients(original_client)


def test_fetch_followees_mid_pagination_failure_keeps_partial(
  monkeypatch, caplog,
):
  """A failed followees page keeps collected pages and logs a warning."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 3))
  source.add(OWNER_ID, 'followees', 0, make_page(0, 200, role='followee'))
  source.add(OWNER_ID, 'followees', 200, make_page(200, 200, role='followee'))
  source.add(OWNER_ID, 'followees', 400, 500)
  expose_warnings(caplog, monkeypatch)

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID)

    assert obj.follower_count() == 3
    assert obj.followee_count() == 400
    assert 'Failed to fetch followees for rider 550564' in caplog.text
    failed = [
      r for r in source.requests
      if r[1] == 'followees' and r[2] == 400
    ]
    assert len(failed) == 1
  finally:
    restore_clients(original_client)


def test_fetch_followees_first_page_failure_keeps_empty(
  monkeypatch, caplog,
):
  """A failed first followees page keeps the list empty with a warning."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 3))
  source.add(OWNER_ID, 'followees', 0, 500)
  expose_warnings(caplog, monkeypatch)

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID)

    assert obj.follower_count() == 3
    assert obj.followees == []
    assert 'Failed to fetch followees for rider 550564' in caplog.text
  finally:
    restore_clients(original_client)


def test_fetch_followees_404_logs_warning_not_raise(monkeypatch, caplog):
  """A followees 404 logs a warning instead of raising (design decision 4)."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 3))
  source.add(OWNER_ID, 'followees', 0, 404)
  expose_warnings(caplog, monkeypatch)

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID)

    assert obj.follower_count() == 3
    assert obj.followees == []
    assert 'Failed to fetch followees for rider 550564' in caplog.text
    assert len(source.requests) == 2
  finally:
    restore_clients(original_client)


def test_fetch_stops_on_malformed_page(monkeypatch, caplog):
  """A non-list page body stops pagination with a warning, no raise."""
  source = PageSource()
  source.add(OWNER_ID, 'followers', 0, make_page(0, 200))
  source.add(OWNER_ID, 'followers', 200, 'not-json')
  expose_warnings(caplog, monkeypatch)

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID, include_followees=False)

    assert obj.follower_count() == 200
    assert len(follower_requests(source)) == 2
    assert 'Unexpected payload for followers of rider 550564' in caplog.text
  finally:
    restore_clients(original_client)


def test_fetch_loop_guard_returns_partial_with_warning(
  monkeypatch, caplog,
):
  """Hitting the pagination cap warns and returns partial data."""
  monkeypatch.setattr(followers_mod, 'PAGE_SIZE', 2)
  monkeypatch.setattr(followers_mod, 'MAX_PAGES', 3)
  source = PageSource()
  for start in (0, 2, 4):
    source.add(OWNER_ID, 'followers', start, make_page(start, 2))
  expose_warnings(caplog, monkeypatch)

  original_client = patch_fetch(source, monkeypatch)
  try:
    obj = ZwiftFollowers()
    obj.fetch(OWNER_ID, include_followees=False)

    assert obj.follower_count() == 6
    assert len(source.requests) == 3
    assert 'Pagination cap' in caplog.text
  finally:
    restore_clients(original_client)


def test_fetch_multiple_paginates_each_rider(monkeypatch):
  """fetch_multiple paginates every rider independently."""
  rider_a = 111111
  rider_b = 222222
  source = PageSource()
  source.add(rider_a, 'followers', 0, make_page(0, 200))
  source.add(rider_a, 'followers', 200, make_page(200, 50))
  source.add(rider_b, 'followers', 0, make_page(0, 3))

  original_client = patch_fetch(source, monkeypatch)
  try:
    results = ZwiftFollowers.fetch_multiple(
      rider_a, rider_b, include_followees=False,
    )

    assert set(results.keys()) == {rider_a, rider_b}
    assert results[rider_a].follower_count() == 250
    assert results[rider_b].follower_count() == 3
    starts_a = [start for start, _ in follower_requests(source, rider_a)]
    starts_b = [start for start, _ in follower_requests(source, rider_b)]
    assert starts_a == [0, 200]
    assert starts_b == [0]
  finally:
    restore_clients(original_client)


def test_fetch_multiple_followers_failure_skips_rider(monkeypatch):
  """A failed followers fetch skips the rider in batch mode."""
  rider_a = 111111
  rider_b = 222222
  source = PageSource()
  source.add(rider_a, 'followers', 0, make_page(0, 3))
  source.add(rider_b, 'followers', 0, 500)

  original_client = patch_fetch(source, monkeypatch)
  try:
    results = ZwiftFollowers.fetch_multiple(
      rider_a, rider_b, include_followees=False,
    )

    assert set(results.keys()) == {rider_a}
    assert results[rider_a].follower_count() == 3
  finally:
    restore_clients(original_client)


def test_fetch_multiple_followees_failure_keeps_partial(
  monkeypatch, caplog,
):
  """A failed followees page in batch mode keeps collected pages."""
  rider_a = 111111
  source = PageSource()
  source.add(rider_a, 'followers', 0, make_page(0, 3))
  source.add(rider_a, 'followees', 0, make_page(0, 200, role='followee'))
  source.add(rider_a, 'followees', 200, make_page(200, 200, role='followee'))
  source.add(rider_a, 'followees', 400, 500)
  expose_warnings(caplog, monkeypatch)

  original_client = patch_fetch(source, monkeypatch)
  try:
    results = ZwiftFollowers.fetch_multiple(rider_a)

    assert set(results.keys()) == {rider_a}
    obj = results[rider_a]
    assert obj.follower_count() == 3
    assert obj.followee_count() == 400
    assert 'Failed to fetch followees for rider 111111' in caplog.text
  finally:
    restore_clients(original_client)
