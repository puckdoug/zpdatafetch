import json

import httpx


def test_cyclist(cyclist):
  assert cyclist is not None


def test_cyclist_initialization(cyclist):
  assert cyclist.raw == {}


def test_cyclist_fetch_single_id(cyclist, login_page, logged_in_page):
  test_data = {
    'data': [
      {'zwid': 123456, 'name': 'Test Cyclist', 'ftp': 250},
    ],
  }

  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if 'profile' in str(request.url) and '_all.json' in str(request.url):
      return httpx.Response(200, text=json.dumps(test_data))
    return httpx.Response(404)

  from zpdatafetch.async_zp import AsyncZP

  # Mock the AsyncZP class to use our test client
  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx.AsyncClient(
      follow_redirects=True,
      transport=httpx.MockTransport(handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    result = cyclist.fetch(123456)
    assert 123456 in result
    assert result[123456] == test_data
  finally:
    AsyncZP.__init__ = original_init


def test_cyclist_fetch_multiple_ids(cyclist, login_page, logged_in_page):
  def handler(request):
    if 'login' in str(request.url) and request.method == 'GET':
      return httpx.Response(200, text=login_page)
    if request.method == 'POST':
      return httpx.Response(200, text=logged_in_page)
    if '123456' in str(request.url) and '_all.json' in str(request.url):
      return httpx.Response(200, text=json.dumps({'id': 123456}))
    if '789012' in str(request.url) and '_all.json' in str(request.url):
      return httpx.Response(200, text=json.dumps({'id': 789012}))
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
    result = cyclist.fetch(123456, 789012)
    assert 123456 in result
    assert 789012 in result
    assert result[123456]['id'] == 123456
    assert result[789012]['id'] == 789012
  finally:
    AsyncZP.__init__ = original_init


def test_cyclist_json_output(cyclist):
  cyclist.raw = {123: json.dumps({'name': 'Test'})}
  json_str = cyclist.json()
  assert '123' in json_str
  assert 'Test' in json_str


def test_cyclist_asdict(cyclist):
  test_json = json.dumps({'name': 'Test'})
  cyclist.raw = {123: test_json}
  assert cyclist.asdict() == {123: test_json}


def test_cyclist_str(cyclist):
  test_json = json.dumps({'name': 'Test'})
  cyclist.raw = {123: test_json}
  assert str(cyclist) == str({123: test_json})


def test_cyclist_raw_attribute_stores_strings(cyclist):
  """Test that raw attribute stores JSON strings, not dicts."""
  from unittest.mock import patch

  from zpdatafetch.async_zp import AsyncZP

  with patch.object(AsyncZP, 'fetch_json') as mock_fetch:
    test_json = '{"id": 123, "name": "Test Cyclist"}'
    mock_fetch.return_value = test_json

    cyclist.fetch(123)

    # raw should be dict[int, str]
    assert isinstance(cyclist.raw, dict)
    assert 123 in cyclist.raw
    assert isinstance(cyclist.raw[123], str)
    assert cyclist.raw[123] == test_json


def test_cyclist_processed_attribute_stores_dicts(cyclist):
  """Test that processed attribute stores parsed dicts."""
  from unittest.mock import patch

  from zpdatafetch.async_zp import AsyncZP

  with patch.object(AsyncZP, 'fetch_json') as mock_fetch:
    test_json = '{"id": 123, "name": "Test Cyclist"}'
    mock_fetch.return_value = test_json

    cyclist.fetch(123)

    # processed should be dict[int, dict]
    assert isinstance(cyclist.processed, dict)
    assert 123 in cyclist.processed
    assert isinstance(cyclist.processed[123], dict)
    assert cyclist.processed[123]['id'] == 123
    assert cyclist.processed[123]['name'] == 'Test Cyclist'


def test_cyclist_raw_preserved_with_malformed_json(cyclist):
  """Test that raw preserves malformed JSON strings."""
  from unittest.mock import patch

  from zpdatafetch.async_zp import AsyncZP

  with patch.object(AsyncZP, 'fetch_json') as mock_fetch:
    malformed_json = '{invalid json}'
    mock_fetch.return_value = malformed_json

    cyclist.fetch(123)

    # raw should still contain the malformed string
    assert 123 in cyclist.raw
    assert cyclist.raw[123] == malformed_json
    # processed should contain empty dict for failed parse
    assert 123 in cyclist.processed
    assert cyclist.processed[123] == {}


def test_cyclist_raw_handles_empty_response(cyclist):
  """Test that raw handles empty response strings."""
  from unittest.mock import patch

  from zpdatafetch.async_zp import AsyncZP

  with patch.object(AsyncZP, 'fetch_json') as mock_fetch:
    mock_fetch.return_value = ''

    cyclist.fetch(123)

    assert 123 in cyclist.raw
    assert cyclist.raw[123] == ''
    assert cyclist.processed[123] == {}
