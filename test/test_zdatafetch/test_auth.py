"""Tests for Zwift API authentication."""

import time

import httpx2
import pytest

from shared.exceptions import AuthenticationError, NetworkError
from zdatafetch.auth import ZwiftAuth


def test_auth_initialization(mock_credentials):
  """Test ZwiftAuth initialization."""
  auth = ZwiftAuth(
    username=mock_credentials['username'],
    password=mock_credentials['password'],
  )

  assert auth.username == mock_credentials['username']
  assert auth.password == mock_credentials['password']
  assert auth.access_token is None
  assert auth.refresh_token is None
  assert auth.access_token_expiration == 0
  assert auth.refresh_token_expiration == 0


def test_login_success(mock_auth, auth_handler, mock_token_response):
  """Test successful login."""
  # Mock the httpx client
  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(auth_handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    mock_auth.login()

    assert mock_auth.access_token == mock_token_response['access_token']
    assert mock_auth.refresh_token == mock_token_response['refresh_token']
    assert mock_auth.expires_in == mock_token_response['expires_in']
    assert (
      mock_auth.refresh_expires_in == mock_token_response['refresh_expires_in']
    )
    assert mock_auth.access_token_expiration > time.time()
    assert mock_auth.refresh_token_expiration > time.time()

  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_login_invalid_credentials(mock_auth):
  """Test login with invalid credentials."""

  def handler(request):
    return httpx2.Response(401, text='Unauthorized')

  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    with pytest.raises(AuthenticationError, match='Invalid Zwift credentials'):
      mock_auth.login()
  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_login_server_error(mock_auth):
  """Test login with server error."""

  def handler(request):
    return httpx2.Response(500, text='Internal Server Error')

  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    with pytest.raises(AuthenticationError, match='Authentication failed'):
      mock_auth.login()
  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_login_network_error(mock_auth):
  """Test login with network error."""

  def handler(request):
    raise httpx2.ConnectError('Connection failed')

  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    with pytest.raises(NetworkError, match='Authentication request failed'):
      mock_auth.login()
  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_login_timeout(mock_auth):
  """Test login timeout."""

  def handler(request):
    raise httpx2.TimeoutException('Request timed out')

  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    with pytest.raises(NetworkError, match='Authentication request timed out'):
      mock_auth.login()
  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_get_access_token_without_login(mock_auth):
  """Test getting access token without logging in first."""
  with pytest.raises(RuntimeError, match='No valid token available'):
    mock_auth.get_access_token()


def test_get_access_token_valid(mock_auth, auth_handler, mock_token_response):
  """Test getting valid access token."""
  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(auth_handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    mock_auth.login()
    token = mock_auth.get_access_token()
    assert token == mock_token_response['access_token']
  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_token_refresh(mock_auth, auth_handler, mock_token_response):
  """Test automatic token refresh."""
  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(auth_handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    mock_auth.login()

    # Manually expire the access token
    mock_auth.access_token_expiration = time.time() - 10

    # Getting the token should trigger a refresh
    token = mock_auth.get_access_token()
    assert token == mock_token_response['access_token']
    assert mock_auth.access_token_expiration > time.time()

  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_is_authenticated(mock_auth, auth_handler):
  """Test authentication status check."""
  import zdatafetch.auth

  original_client = httpx2.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx2.MockTransport(auth_handler))

  zdatafetch.auth.httpx2.Client = mock_client

  try:
    # Not authenticated initially
    assert not mock_auth.is_authenticated()

    # Authenticated after login
    mock_auth.login()
    assert mock_auth.is_authenticated()

    # Still authenticated if tokens haven't expired
    assert mock_auth.is_authenticated()

    # Not authenticated if both tokens expired
    mock_auth.access_token_expiration = time.time() - 10
    mock_auth.refresh_token_expiration = time.time() - 10
    assert not mock_auth.is_authenticated()

  finally:
    zdatafetch.auth.httpx2.Client = original_client


def test_parse_token_response(mock_auth, mock_token_response):
  """Test parsing of token response."""
  now = time.time()
  mock_auth._parse_token_response(mock_token_response)

  assert mock_auth.access_token == mock_token_response['access_token']
  assert mock_auth.refresh_token == mock_token_response['refresh_token']
  assert mock_auth.expires_in == mock_token_response['expires_in']
  assert (
    mock_auth.refresh_expires_in == mock_token_response['refresh_expires_in']
  )

  # Check expiration timestamps are set correctly (with 5 second buffer)
  assert mock_auth.access_token_expiration > now
  assert (
    mock_auth.access_token_expiration <= now + mock_token_response['expires_in']
  )
  assert mock_auth.refresh_token_expiration > now
  assert (
    mock_auth.refresh_token_expiration
    <= now + mock_token_response['refresh_expires_in']
  )


def test_token_response_with_kebab_case(mock_auth):
  """Test parsing token response with kebab-case keys."""
  token_response = {
    'access-token': 'test_token',
    'refresh-token': 'test_refresh',
    'expires-in': 3600,
  }

  mock_auth._parse_token_response(token_response)

  # Verify kebab-case converted to snake_case
  assert mock_auth.access_token == 'test_token'
  assert mock_auth.refresh_token == 'test_refresh'
  assert mock_auth.expires_in == 3600
