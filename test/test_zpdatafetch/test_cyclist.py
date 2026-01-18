import json

import httpx


def test_cyclist_sync_mode():
  """Test that sync mode can be enabled and disabled."""
  from zpdatafetch import Cyclist

  # Default should be False
  assert Cyclist._sync_mode is False

  # Enable sync mode
  Cyclist.set_sync_mode(True)
  assert Cyclist._sync_mode is True

  # Disable sync mode
  Cyclist.set_sync_mode(False)
  assert Cyclist._sync_mode is False


def test_cyclist_sync_mode_fetch(cyclist, login_page, logged_in_page):
  """Test that sync mode uses synchronous fetch path."""
  from zpdatafetch import Cyclist
  from zpdatafetch.zp import ZP

  test_data = {"data": [{"zwid": 123456, "name": "Test Cyclist"}]}

  def handler(request):
    if "login" in str(request.url) and request.method == "GET":
      return httpx.Response(200, text=login_page)
    if request.method == "POST":
      return httpx.Response(200, text=logged_in_page)
    if "profile" in str(request.url) and "_all.json" in str(request.url):
      return httpx.Response(200, text=json.dumps(test_data))
    return httpx.Response(404)

  # Enable sync mode
  Cyclist.set_sync_mode(True)

  # Mock the ZP client (sync)
  original_init = ZP.__init__

  def mock_init(self, skip_credential_check=False, shared_client=False):
    original_init(self, skip_credential_check=True, shared_client=False)
    self._client = httpx.Client(
      follow_redirects=True,
      transport=httpx.MockTransport(handler),
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
    Cyclist.set_sync_mode(False)  # Reset for other tests


def test_cyclist(cyclist):
  assert cyclist is not None


def test_cyclist_initialization(cyclist):
  assert cyclist._raw == {}


def test_cyclist_fetch_single_id(cyclist, login_page, logged_in_page):
  test_data = {
    "data": [
      {"zwid": 123456, "name": "Test Cyclist", "ftp": 250},
    ],
  }

  def handler(request):
    if "login" in str(request.url) and request.method == "GET":
      return httpx.Response(200, text=login_page)
    if request.method == "POST":
      return httpx.Response(200, text=logged_in_page)
    if "profile" in str(request.url) and "_all.json" in str(request.url):
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
    from zpdatafetch.zpcyclist import ZPCyclist

    result = cyclist.fetch(123456)
    assert 123456 in result
    assert isinstance(result[123456], ZPCyclist)
    assert result[123456].asdict() == test_data
  finally:
    AsyncZP.__init__ = original_init


def test_cyclist_fetch_multiple_ids(cyclist, login_page, logged_in_page):
  def handler(request):
    if "login" in str(request.url) and request.method == "GET":
      return httpx.Response(200, text=login_page)
    if request.method == "POST":
      return httpx.Response(200, text=logged_in_page)
    if "123456" in str(request.url) and "_all.json" in str(request.url):
      return httpx.Response(200, text=json.dumps({"id": 123456}))
    if "789012" in str(request.url) and "_all.json" in str(request.url):
      return httpx.Response(200, text=json.dumps({"id": 789012}))
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
    assert result[123456]["id"] == 123456
    assert result[789012]["id"] == 789012
  finally:
    AsyncZP.__init__ = original_init


def test_cyclist_json_output(cyclist):
  cyclist._fetched = {123: json.dumps({"name": "Test"})}
  json_str = cyclist.json()
  assert "123" in json_str
  assert "Test" in json_str


def test_cyclist_asdict(cyclist):
  test_json = json.dumps({"name": "Test"})
  cyclist._fetched = {123: test_json}
  assert cyclist.asdict() == {123: test_json}


def test_cyclist_str(cyclist):
  test_json = json.dumps({"name": "Test"})
  cyclist._fetched = {123: test_json}
  assert str(cyclist) == str({123: test_json})


def test_cyclist_raw_attribute_stores_strings(cyclist):
  """Test that raw attribute stores JSON strings, not dicts."""
  from unittest.mock import AsyncMock, patch

  from zpdatafetch.async_zp import AsyncZP

  with (
    patch.object(AsyncZP, "login", new_callable=AsyncMock),
    patch.object(AsyncZP, "fetch_json", new_callable=AsyncMock) as mock_fetch,
  ):
    test_json = '{"id": 123, "name": "Test Cyclist"}'
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
    patch.object(AsyncZP, "login", new_callable=AsyncMock),
    patch.object(AsyncZP, "fetch_json", new_callable=AsyncMock) as mock_fetch,
  ):
    test_json = '{"id": 123, "name": "Test Cyclist"}'
    mock_fetch.return_value = test_json

    cyclist.fetch(123)

    # _fetched should be dict[int, ZPCyclist]
    from zpdatafetch.zpcyclist import ZPCyclist

    assert isinstance(cyclist._fetched, dict)
    assert 123 in cyclist._fetched
    assert isinstance(cyclist._fetched[123], ZPCyclist)
    assert cyclist._fetched[123]["id"] == 123
    assert cyclist._fetched[123]["name"] == "Test Cyclist"


def test_cyclist_raw_preserved_with_malformed_json(cyclist):
  """Test that raw preserves malformed JSON strings."""
  from unittest.mock import AsyncMock, patch

  from zpdatafetch.async_zp import AsyncZP

  with (
    patch.object(AsyncZP, "login", new_callable=AsyncMock),
    patch.object(AsyncZP, "fetch_json", new_callable=AsyncMock) as mock_fetch,
  ):
    malformed_json = "{invalid json}"
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
    patch.object(AsyncZP, "login", new_callable=AsyncMock),
    patch.object(AsyncZP, "fetch_json", new_callable=AsyncMock) as mock_fetch,
  ):
    mock_fetch.return_value = ""

    cyclist.fetch(123)

    from zpdatafetch.zpcyclist import ZPCyclist

    assert 123 in cyclist._raw
    assert cyclist._raw[123] == ""
    assert isinstance(cyclist._fetched[123], ZPCyclist)
    assert cyclist._fetched[123].asdict() == {}
