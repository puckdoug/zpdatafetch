"""Tests for the async ZP API."""

import sys

import httpx
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zp import ZPAuthenticationError, ZPConfigError, ZPNetworkError


@pytest.fixture
async def async_zp():
  """Create AsyncZP instance for testing."""
  zp = AsyncZP(skip_credential_check=True)
  yield zp
  await zp.close()


@pytest.mark.anyio
async def test_async_init_without_credentials():
  """Test AsyncZP initialization fails without credentials."""
  import zpdatafetch.config

  original_config_init = zpdatafetch.config.Config.__init__

  def mock_config_init(self):
    original_config_init(self)
    self.username = ''
    self.password = ''

  zpdatafetch.config.Config.__init__ = mock_config_init

  try:
    with pytest.raises(ZPConfigError):
      AsyncZP()
  finally:
    zpdatafetch.config.Config.__init__ = original_config_init


@pytest.mark.anyio
async def test_async_init_with_skip_credential_check():
  """Test AsyncZP can be initialized when skipping credential check."""
  zp = AsyncZP(skip_credential_check=True)
  assert zp is not None
  await zp.close()


@pytest.mark.anyio
async def test_async_context_manager():
  """Test AsyncZP works as async context manager."""
  async with AsyncZP(skip_credential_check=True) as zp:
    assert zp is not None
    assert isinstance(zp, AsyncZP)


@pytest.mark.anyio
async def test_async_login_success(login_page, logged_in_page):
  """Test successful async login."""

  def handler(request):
    match request.method:
      case 'GET':
        return httpx.Response(200, text=login_page)
      case 'POST':
        return httpx.Response(200, text=logged_in_page)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )
    await zp.login()
    assert zp.login_response is not None
    assert zp.login_response.status_code == 200


@pytest.mark.anyio
async def test_async_login_missing_form():
  """Test login fails when form is missing."""

  def handler(request):
    return httpx.Response(200, text='<html><body>No form here</body></html>')

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )
    with pytest.raises(ZPAuthenticationError, match='Login form not found'):
      await zp.login()


@pytest.mark.anyio
async def test_async_login_network_error():
  """Test login handles network errors."""

  def handler(request):
    raise httpx.ConnectError('Connection failed')

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )
    with pytest.raises(ZPNetworkError, match='Network error during login'):
      await zp.login()


@pytest.mark.anyio
async def test_async_fetch_json_success():
  """Test successful async JSON fetch."""
  test_data = {'key': 'value', 'number': 42}

  def handler(request):
    if 'login' in str(request.url):
      return httpx.Response(
        200,
        text='<html><form action="/login"></form></html>',
      )
    return httpx.Response(200, json=test_data)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )
    result = await zp.fetch_json('https://zwiftpower.com/api/test')
    assert result == test_data


@pytest.mark.anyio
async def test_async_fetch_json_invalid_json():
  """Test fetch_json handles invalid JSON gracefully."""

  def handler(request):
    if 'login' in str(request.url):
      return httpx.Response(
        200,
        text='<html><form action="/login"></form></html>',
      )
    return httpx.Response(200, text='This is not JSON')

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )
    result = await zp.fetch_json('https://zwiftpower.com/api/test')
    assert result == {}


@pytest.mark.anyio
async def test_async_fetch_page_success():
  """Test successful async page fetch."""
  test_html = '<html><body>Test Page</body></html>'

  def handler(request):
    if 'login' in str(request.url):
      return httpx.Response(
        200,
        text='<html><form action="/login"></form></html>',
      )
    return httpx.Response(200, text=test_html)

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )
    result = await zp.fetch_page('https://zwiftpower.com/page/test')
    assert result == test_html


@pytest.mark.anyio
async def test_async_retry_on_transient_error():
  """Test retry logic on transient errors."""
  call_count = 0

  def handler(request):
    nonlocal call_count
    if 'login' in str(request.url):
      return httpx.Response(
        200,
        text='<html><form action="/login"></form></html>',
      )

    call_count += 1
    if call_count == 1:
      # First call fails
      return httpx.Response(500, text='Server Error')
    # Second call succeeds
    return httpx.Response(200, json={'status': 'ok'})

  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.MockTransport(handler),
      ),
    )
    result = await zp.fetch_json('https://zwiftpower.com/api/test')
    assert result == {'status': 'ok'}
    assert call_count == 2  # Verify retry happened


@pytest.mark.anyio
async def test_async_clear_credentials():
  """Test credential clearing."""
  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    zp.clear_credentials()
    assert zp.username == ''
    assert zp.password == ''


@pytest.mark.anyio
async def test_async_static_methods():
  """Test static helper methods."""
  assert AsyncZP.set_pen(0) == 'none'
  assert AsyncZP.set_pen(10) == 'time'
  assert AsyncZP.set_pen(30) == 'DSQ'
  assert AsyncZP.set_pen(99) == 'unknown'

  assert AsyncZP.set_rider_category(10) == 'A'
  assert AsyncZP.set_rider_category(20) == 'B'
  assert AsyncZP.set_rider_category(30) == 'C'
  assert AsyncZP.set_rider_category(99) == 'unknown'

  assert AsyncZP.set_category(10) == 'A'
  assert AsyncZP.set_category(40) == 'D'


@pytest.mark.anyio
async def test_async_login_url():
  """Test login URL getter/setter."""
  async with AsyncZP(skip_credential_check=True) as zp:
    original_url = zp.login_url()
    assert original_url == (
      'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
    )

    new_url = 'https://test.example.com/login'
    zp.login_url(new_url)
    assert zp.login_url() == new_url


@pytest.mark.xfail(
  sys.version_info >= (3, 14),
  reason='httpcore 1.1.x incompatible with Python 3.14 typing.Union - '
  'upstream issue encode/httpcore, fixed in 1.2.0+',
  strict=False,
)
@pytest.mark.anyio
async def test_async_shared_client():
  """Test shared client functionality."""
  # Create first instance with shared client
  zp1 = AsyncZP(skip_credential_check=True, shared_client=True)

  # Shared client should be created
  assert AsyncZP._shared_client is not None

  # Create second instance with shared client
  zp2 = AsyncZP(skip_credential_check=True, shared_client=True)

  # Both should use same client
  await zp1.init_client()
  await zp2.init_client()
  assert zp1._client is zp2._client

  # Close instances (should not close shared client)
  await zp1.close()
  await zp2.close()

  # Close shared session
  await AsyncZP.close_shared_session()
  assert AsyncZP._shared_client is None
