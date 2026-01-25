"""Zwift API authentication handling.

Manages OAuth2 authentication with Zwift's unofficial API, including
token acquisition, storage, and automatic refresh.
"""

import time
from typing import Any

import httpx

from shared.exceptions import AuthenticationError, NetworkError
from zdatafetch.logging_config import get_logger

logger = get_logger(__name__)


class ZwiftAuth:
  """Handles Zwift API authentication and token management.

  Implements OAuth2 password grant flow for Zwift's unofficial API.
  Automatically handles token refresh when access tokens expire.

  Based on reverse-engineered Zwift mobile API.

  Usage:
      auth = ZwiftAuth(username, password)
      auth.login()
      token = auth.get_access_token()

  Attributes:
      username: Zwift account username/email
      password: Zwift account password
      access_token: Current OAuth2 access token
      refresh_token: OAuth2 refresh token for obtaining new access tokens
      access_token_expiration: Timestamp when access token expires
      refresh_token_expiration: Timestamp when refresh token expires
  """

  AUTH_URL = 'https://secure.zwift.com/auth/realms/zwift/tokens/access/codes'
  CLIENT_ID = 'Zwift_Mobile_Link'

  def __init__(self, username: str, password: str) -> None:
    """Initialize auth handler with credentials.

    Args:
        username: Zwift account username/email
        password: Zwift account password
    """
    self.username = username
    self.password = password
    self.access_token: str | None = None
    self.refresh_token: str | None = None
    self.access_token_expiration: float = 0
    self.refresh_token_expiration: float = 0
    self.expires_in: int = 0
    self.refresh_expires_in: int = 0

  def login(self) -> None:
    """Authenticate with Zwift and obtain access token.

    Makes initial password grant request to get OAuth2 tokens.

    Raises:
        AuthenticationError: If login fails (invalid credentials, etc.)
        NetworkError: If network request fails
    """
    logger.info('Authenticating with Zwift API')

    data = {
      'username': self.username,
      'password': self.password,
      'grant_type': 'password',
      'client_id': self.CLIENT_ID,
    }

    try:
      with httpx.Client() as client:
        response = client.post(self.AUTH_URL, data=data, timeout=30.0)

        if response.status_code == 401:
          raise AuthenticationError('Invalid Zwift credentials')
        if response.status_code != 200:
          raise AuthenticationError(
            f'Authentication failed with status {response.status_code}: {response.text}',
          )

        self._parse_token_response(response.json())

      logger.info(
        f'Authentication successful (token expires in {self.expires_in}s)',
      )

    except httpx.TimeoutException as e:
      raise NetworkError(f'Authentication request timed out: {e}') from e
    except httpx.HTTPError as e:
      raise NetworkError(f'Authentication request failed: {e}') from e

  def _parse_token_response(self, token_data: dict[str, Any]) -> None:
    """Parse token response and store values.

    Args:
        token_data: JSON response from auth endpoint
    """
    now = time.time()

    # Store all response fields as attributes
    for key, value in token_data.items():
      # Convert kebab-case to snake_case
      attr_name = key.replace('-', '_')
      setattr(self, attr_name, value)

    # Calculate expiration timestamps (with 5 second buffer)
    if hasattr(self, 'expires_in'):
      self.access_token_expiration = now + self.expires_in - 5
    if hasattr(self, 'refresh_expires_in'):
      self.refresh_token_expiration = now + self.refresh_expires_in - 5

  def get_access_token(self) -> str:
    """Get a valid access token, refreshing if necessary.

    Automatically refreshes the access token if it has expired but
    the refresh token is still valid.

    Returns:
        Valid OAuth2 access token string

    Raises:
        RuntimeError: If no token available and refresh fails
        AuthenticationError: If token refresh fails
        NetworkError: If network request fails
    """
    now = time.time()

    # Check if access token is still valid
    if self.access_token and now < self.access_token_expiration:
      return self.access_token

    # Check if we can refresh
    if self.refresh_token and now < self.refresh_token_expiration:
      self._refresh_token()
      if self.access_token:
        return self.access_token

    raise RuntimeError(
      'No valid token available. Call login() first or re-authenticate.',
    )

  def _refresh_token(self) -> None:
    """Refresh the access token using refresh token.

    Raises:
        AuthenticationError: If token refresh fails
        NetworkError: If network request fails
    """
    logger.debug('Refreshing access token')

    data = {
      'refresh_token': self.refresh_token,
      'grant_type': 'refresh_token',
      'client_id': self.CLIENT_ID,
    }

    try:
      with httpx.Client() as client:
        response = client.post(self.AUTH_URL, data=data, timeout=30.0)

        if response.status_code == 401:
          raise AuthenticationError(
            'Token refresh failed - authentication required',
          )
        if response.status_code != 200:
          raise AuthenticationError(
            f'Token refresh failed with status {response.status_code}: {response.text}',
          )

        self._parse_token_response(response.json())

      logger.debug('Token refreshed successfully')

    except httpx.TimeoutException as e:
      raise NetworkError(f'Token refresh request timed out: {e}') from e
    except httpx.HTTPError as e:
      raise NetworkError(f'Token refresh request failed: {e}') from e

  def is_authenticated(self) -> bool:
    """Check if currently authenticated with valid tokens.

    Returns:
        True if we have valid access or refresh tokens, False otherwise
    """
    now = time.time()
    return bool(
      (self.access_token and now < self.access_token_expiration)
      or (self.refresh_token and now < self.refresh_token_expiration),
    )
