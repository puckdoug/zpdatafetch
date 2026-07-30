import json

import httpx2

from zpdatafetch.zpcyclist import ZPCyclist


def test_zpcyclist_empty_instantiation():
  """Test that ZPCyclist can be instantiated with no arguments."""
  obj = ZPCyclist()
  assert obj is not None
  assert obj.asdict() == {}


def test_cyclist_sync_mode():
  """Test that sync mode can be enabled and disabled."""
  from zpdatafetch import ZPCyclistFetch

  # Default should be False
  assert ZPCyclistFetch._sync_mode is False

  # Enable sync mode
  ZPCyclistFetch.set_sync_mode(True)
  assert ZPCyclistFetch._sync_mode is True

  # Disable sync mode
  ZPCyclistFetch.set_sync_mode(False)
  assert ZPCyclistFetch._sync_mode is False


def test_cyclist_sync_mode_fetch(cyclist, login_page, logged_in_page):
  """Test that sync mode uses synchronous fetch path."""
  from zpdatafetch import ZPCyclistFetch
  from zpdatafetch.zp import ZP

  test_data = {'data': [{'zwid': 123456, 'name': 'Test ZPCyclistFetch'}]}

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'profile' in str(request.url) and '_all.json' in str(request.url):
      return httpx2.Response(200, text=json.dumps(test_data))
    return httpx2.Response(404)

  # Enable sync mode
  ZPCyclistFetch.set_sync_mode(True)

  # Mock the ZP client (sync)
  original_init = ZP.__init__

  def mock_init(self, skip_credential_check=False, shared_client=False):
    original_init(self, skip_credential_check=True, shared_client=False)
    self._client = httpx2.Client(
      follow_redirects=True,
      transport=httpx2.MockTransport(handler),
    )

  ZP.__init__ = mock_init

  try:
    from zpdatafetch.zpcyclist import ZPCyclist

    result = cyclist.fetch(123456)
    assert 123456 in result
    assert isinstance(result[123456], ZPCyclist)
    assert result[123456].asdict() == test_data
  finally:
    ZP.__init__ = original_init
    ZPCyclistFetch.set_sync_mode(False)  # Reset for other tests


def test_cyclist(cyclist):
  assert cyclist is not None


def test_cyclist_initialization(cyclist):
  assert cyclist._raw == {}


def test_cyclist_fetch_single_id(cyclist, login_page, logged_in_page):
  test_data = {
    'data': [
      {
        'zwid': 123456,
        'name': 'Test ZPCyclistFetch',
        'ftp': 250,
        'tid': 999,
        'tname': 'Test Team',
        'male': 1,
        'div': 20,
        'divw': 0,
        'height': 180,
        'weight': 75.0,
        'skill': 450.5,
        'age': '35',
      },
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if 'profile' in str(request.url) and '_all.json' in str(request.url):
      return httpx2.Response(200, text=json.dumps(test_data))
    return httpx2.Response(404)

  from zpdatafetch.async_zp import AsyncZP

  # Mock the AsyncZP class to use our test client
  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx2.AsyncClient(
      follow_redirects=True,
      transport=httpx2.MockTransport(handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    from zpdatafetch.zpcyclist import ZPCyclist

    result = cyclist.fetch(123456)
    assert 123456 in result
    assert isinstance(result[123456], ZPCyclist)
    assert result[123456].asdict() == test_data

    # Test extracted fields from last race entry
    cyclist_obj = result[123456]
    assert cyclist_obj.zwift_id == 123456
    assert cyclist_obj.name == 'Test ZPCyclistFetch'
    assert cyclist_obj.team_id == 999
    assert cyclist_obj.team_name == 'Test Team'
    assert cyclist_obj.gender == 'male'
    assert cyclist_obj.category == 'B'
    assert cyclist_obj.category_women == ''
    assert cyclist_obj.zftp == 250
    assert cyclist_obj.height == 180
    assert cyclist_obj.weight == 75.0
    assert cyclist_obj.skill == 450.5
    assert cyclist_obj.age == '35'
  finally:
    AsyncZP.__init__ = original_init


def test_cyclist_fetch_multiple_ids(cyclist, login_page, logged_in_page):
  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx2.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx2.Response(200, text=logged_in_page)
    if '123456' in str(request.url) and '_all.json' in str(request.url):
      return httpx2.Response(200, text=json.dumps({'id': 123456}))
    if '789012' in str(request.url) and '_all.json' in str(request.url):
      return httpx2.Response(200, text=json.dumps({'id': 789012}))
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
    result = cyclist.fetch(123456, 789012)
    assert 123456 in result
    assert 789012 in result
    assert result[123456]['id'] == 123456
    assert result[789012]['id'] == 789012
  finally:
    AsyncZP.__init__ = original_init


def test_cyclist_json_output(cyclist):
  cyclist._fetched = {123: json.dumps({'name': 'Test'})}
  json_str = cyclist.json()
  assert '123' in json_str
  assert 'Test' in json_str


def test_cyclist_asdict(cyclist):
  test_json = json.dumps({'name': 'Test'})
  cyclist._fetched = {123: test_json}
  assert cyclist.asdict() == {123: test_json}


def test_cyclist_str(cyclist):
  test_json = json.dumps({'name': 'Test'})
  cyclist._fetched = {123: test_json}
  assert str(cyclist) == str({123: test_json})


def test_cyclist_raw_attribute_stores_strings(cyclist):
  """Test that raw attribute stores JSON strings, not dicts."""
  from unittest.mock import AsyncMock, patch

  from zpdatafetch.async_zp import AsyncZP

  with (
    patch.object(AsyncZP, 'login', new_callable=AsyncMock),
    patch.object(AsyncZP, 'fetch_json', new_callable=AsyncMock) as mock_fetch,
  ):
    test_json = '{"id": 123, "name": "Test ZPCyclistFetch"}'
    mock_fetch.return_value = test_json

    cyclist.fetch(123)

    # raw should be dict[int, str]
    assert isinstance(cyclist._raw, dict)
    assert 123 in cyclist._raw
    assert isinstance(cyclist._raw[123], str)
    assert cyclist._raw[123] == test_json


def test_cyclist_processed_attribute_stores_dicts(cyclist):
  """Test that processed attribute stores parsed dicts."""
  from unittest.mock import AsyncMock, patch

  from zpdatafetch.async_zp import AsyncZP

  with (
    patch.object(AsyncZP, 'login', new_callable=AsyncMock),
    patch.object(AsyncZP, 'fetch_json', new_callable=AsyncMock) as mock_fetch,
  ):
    test_json = '{"id": 123, "name": "Test ZPCyclistFetch"}'
    mock_fetch.return_value = test_json

    cyclist.fetch(123)

    # _fetched should be dict[int, ZPCyclist]
    from zpdatafetch.zpcyclist import ZPCyclist

    assert isinstance(cyclist._fetched, dict)
    assert 123 in cyclist._fetched
    assert isinstance(cyclist._fetched[123], ZPCyclist)
    assert cyclist._fetched[123]['id'] == 123
    assert cyclist._fetched[123]['name'] == 'Test ZPCyclistFetch'


def test_cyclist_raw_preserved_with_malformed_json(cyclist):
  """Test that raw preserves malformed JSON strings."""
  from unittest.mock import AsyncMock, patch

  from zpdatafetch.async_zp import AsyncZP

  with (
    patch.object(AsyncZP, 'login', new_callable=AsyncMock),
    patch.object(AsyncZP, 'fetch_json', new_callable=AsyncMock) as mock_fetch,
  ):
    malformed_json = '{invalid json}'
    mock_fetch.return_value = malformed_json

    cyclist.fetch(123)

    # raw should still contain the malformed string
    from zpdatafetch.zpcyclist import ZPCyclist

    assert 123 in cyclist._raw
    assert cyclist._raw[123] == malformed_json
    # _fetched should contain ZPCyclist wrapping empty dict for failed parse
    assert 123 in cyclist._fetched
    assert isinstance(cyclist._fetched[123], ZPCyclist)
    assert cyclist._fetched[123].asdict() == {}


def test_cyclist_raw_handles_empty_response(cyclist):
  """Test that raw handles empty response strings."""
  from unittest.mock import AsyncMock, patch

  from zpdatafetch.async_zp import AsyncZP

  with (
    patch.object(AsyncZP, 'login', new_callable=AsyncMock),
    patch.object(AsyncZP, 'fetch_json', new_callable=AsyncMock) as mock_fetch,
  ):
    mock_fetch.return_value = ''

    cyclist.fetch(123)

    from zpdatafetch.zpcyclist import ZPCyclist

    assert 123 in cyclist._raw
    assert cyclist._raw[123] == ''
    assert isinstance(cyclist._fetched[123], ZPCyclist)
    assert cyclist._fetched[123].asdict() == {}


def test_cyclist_extracts_fields_from_last_race():
  """Test that cyclist extracts key fields from the last race entry."""
  from zpdatafetch.zpcyclist import ZPCyclist

  test_data = {
    'data': [
      {
        'zwid': 123,
        'name': 'First Race',
        'ftp': 200,
        'tid': 100,
        'tname': 'Old Team',
        'male': 0,
        'div': 30,
        'divw': 20,
        'height': 165,
        'weight': 60.0,
        'skill': 300.0,
        'age': '30',
      },
      {
        'zwid': 123,
        'name': 'Last Race',
        'ftp': 250,
        'tid': 999,
        'tname': 'New Team',
        'male': 1,
        'div': 20,
        'divw': 10,
        'height': 180,
        'weight': 75.0,
        'skill': 450.5,
        'age': '35',
      },
    ],
  }

  cyclist = ZPCyclist.from_dict(test_data)

  # Should extract from last race (index -1)
  assert cyclist.zwift_id == 123
  assert cyclist.name == 'Last Race'
  assert cyclist.team_id == 999
  assert cyclist.team_name == 'New Team'
  assert cyclist.gender == 'male'
  assert cyclist.category == 'B'
  assert cyclist.category_women == 'A'
  assert cyclist.zftp == 250
  assert cyclist.height == 180
  assert cyclist.weight == 75.0
  assert cyclist.skill == 450.5
  assert cyclist.age == '35'


def test_cyclist_handles_missing_data():
  """Test that cyclist handles missing data array gracefully."""
  from zpdatafetch.zpcyclist import ZPCyclist

  test_data = {'zwid': 123, 'name': 'Test'}

  cyclist = ZPCyclist.from_dict(test_data)

  # All fields should be defaults
  assert cyclist.zwift_id == 0
  assert cyclist.name == ''
  assert cyclist.team_id is None
  assert cyclist.team_name is None
  assert cyclist.gender == ''
  assert cyclist.category == ''
  assert cyclist.category_women == ''
  assert cyclist.zftp == 0
  assert cyclist.height == 0
  assert cyclist.weight == 0.0
  assert cyclist.skill == 0.0
  assert cyclist.age == ''


def test_cyclist_handles_empty_data_array():
  """Test that cyclist handles empty data array gracefully."""
  from zpdatafetch.zpcyclist import ZPCyclist

  test_data = {'data': []}

  cyclist = ZPCyclist.from_dict(test_data)

  # All fields should be defaults
  assert cyclist.zwift_id == 0
  assert cyclist.name == ''
  assert cyclist.team_id is None
  assert cyclist.team_name is None
  assert cyclist.gender == ''
  assert cyclist.category == ''
  assert cyclist.category_women == ''
  assert cyclist.zftp == 0
  assert cyclist.height == 0
  assert cyclist.weight == 0.0
  assert cyclist.skill == 0.0
  assert cyclist.age == ''


def test_cyclist_handles_array_values():
  """Test that cyclist correctly extracts values from array fields."""
  from zpdatafetch.zpcyclist import ZPCyclist

  test_data = {
    'data': [
      {
        'zwid': 123,
        'ftp': [250, 1],  # Array format
        'male': [1, 0],
        'div': [20, 0],
        'divw': [10, 0],
        'height': [180, 0],
        'weight': [75.0, 0],
        'skill': [450.5, 0],
        'tid': 999,
        'tname': 'Test Team',
        'age': '35',
      },
    ],
  }

  cyclist = ZPCyclist.from_dict(test_data)

  # Should extract first element from arrays
  assert cyclist.zwift_id == 123
  assert cyclist.zftp == 250
  assert cyclist.gender == 'male'
  assert cyclist.category == 'B'
  assert cyclist.category_women == 'A'
  assert cyclist.height == 180
  assert cyclist.weight == 75.0
  assert cyclist.skill == 450.5
