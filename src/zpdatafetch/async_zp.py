"""Async version of the ZP class for asynchronous Zwiftpower API access.

This module provides async/await compatible interfaces for the Zwiftpower API,
allowing for concurrent requests and better performance in async applications.
"""

from typing import Any

import httpx
from bs4 import BeautifulSoup

from shared.error_helpers import format_auth_error, format_network_error
from shared.exceptions import (
  AuthenticationError,
  ConfigError,
  NetworkError,
)
from shared.http_client import AsyncBaseHTTPClient, fetch_with_retry_async
from zpdatafetch.config import Config
from zpdatafetch.logging_config import get_logger

logger = get_logger(__name__)


# ==============================================================================
class AsyncZP(AsyncBaseHTTPClient):
  """Async version of the core ZP class for interacting with Zwiftpower API.

  This class provides async/await compatible methods for authentication,
  session management, and HTTP requests to Zwiftpower. It can be used with
  asyncio for concurrent operations.

  Usage:
    async with AsyncZP() as zp:
      data = await zp.fetch_json('https://zwiftpower.com/...')

  Or:
    zp = AsyncZP()
    await zp.login()
    data = await zp.fetch_json('https://zwiftpower.com/...')
    await zp.close()

  Attributes:
    username: Zwiftpower username loaded from keyring
    password: Zwiftpower password loaded from keyring
    login_response: Response from the login POST request
  """

  _client: httpx.AsyncClient | None = None
  _login_url: str = (
    'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
  )
  _shared_client: httpx.AsyncClient | None = None
  _owns_client: bool = False

  # ----------------------------------------------------------------------------
  def __init__(
    self,
    skip_credential_check: bool = False,
    shared_client: bool = False,
  ) -> None:
    """Initialize the AsyncZP client with credentials from keyring.

    Args:
      skip_credential_check: Skip validation of credentials (used for testing)
      shared_client: Use a shared HTTP client for connection pooling (default: False).
        Useful when creating multiple AsyncZP instances for batch operations.

    Raises:
      ConfigError: If credentials are not found in keyring
    """
    self.config: Config = Config()
    self.config.load()
    self.username: str = self.config.username
    self.password: str = self.config.password
    self.login_response: httpx.Response | None = None

    if not skip_credential_check and (not self.username or not self.password):
      raise ConfigError(
        'Zwiftpower credentials not found. Please run "zpdata config" to set up your credentials.',
      )

    self._owns_client = not shared_client
    # Initialize shared client immediately (non-async)
    # This ensures _shared_client is available for tests
    if shared_client and AsyncZP._shared_client is None:
      logger.debug('Creating shared async HTTP client for connection pooling')
      AsyncZP._shared_client = httpx.AsyncClient(
        follow_redirects=True,
        verify=True,
      )

  # ----------------------------------------------------------------------------
  def clear_credentials(self) -> None:
    """Securely clear credentials from memory.

    Overwrites credential strings before deletion to reduce risk of recovery
    from memory dumps. Should be called when credentials are no longer needed.

    SECURITY: This method helps prevent credentials from being exposed if the
    process is dumped or inspected while credentials are in memory.
    """
    logger.debug('Clearing credentials from memory')
    # Overwrite credentials with dummy data before deletion
    if self.username:
      self.username = '*' * len(self.username)
      self.username = ''
    if self.password:
      self.password = '*' * len(self.password)
      self.password = ''
    logger.debug('Credentials cleared')

  # ----------------------------------------------------------------------------
  async def login(self) -> None:
    """Authenticate with Zwiftpower and establish an async session.

    Fetches the login page, extracts the login form URL, and submits
    credentials to authenticate. Sets login_response with the result.

    Raises:
      NetworkError: If network requests fail
      AuthenticationError: If login form cannot be parsed or auth fails
    """
    logger.info('Logging in to Zwiftpower (async)')

    if not self._client:
      await self.init_client()
    assert self._client is not None

    try:
      logger.debug(f'Fetching url: {self._login_url}')
      page = await self._client.get(self._login_url)
      page.raise_for_status()
    except httpx.HTTPStatusError as e:
      logger.error(f'Failed to fetch login page: {e}')
      raise NetworkError(
        format_network_error(
          'fetch login page',
          self._login_url,
          e,
          status_code=e.response.status_code,
        ),
      ) from e
    except httpx.RequestError as e:
      logger.error(f'Network error during login: {e}')
      raise NetworkError(
        format_network_error('fetch login page', self._login_url, e),
      ) from e

    self._client.cookies.get('phpbb3_lswlk_sid')

    try:
      soup = BeautifulSoup(page.text, 'lxml')
      if not soup.form or 'action' not in soup.form.attrs:
        logger.error('Login form not found on page')
        raise AuthenticationError(
          format_auth_error(
            'parse login form',
            self._login_url,
            Exception('Login form not found on page'),
            suggestion='Zwiftpower may have changed their login flow. Contact support if this persists.',
          ),
        )
      login_url_from_form = soup.form['action'][0:]
      logger.debug(f'Extracted login form URL: {login_url_from_form}')
    except (AttributeError, KeyError) as e:
      logger.error(f'Could not parse login form: {e}')
      raise AuthenticationError(
        format_auth_error(
          'parse login form',
          self._login_url,
          e,
          suggestion='The login page structure may have changed. Check Zwiftpower is working normally.',
        ),
      ) from e

    data = {'username': self.username, 'password': self.password}
    # SECURITY: Do NOT log the data dict or login URL - it contains credentials
    logger.debug('Submitting authentication credentials to login endpoint')

    try:
      self.login_response = await self._client.post(
        login_url_from_form,
        data=data,
        cookies=self._client.cookies,
      )
      self.login_response.raise_for_status()

      # Check if login was actually successful
      if 'ucp.php' in str(self.login_response.url) and 'mode=login' in str(
        self.login_response.url,
      ):
        logger.error('Authentication failed - redirected back to login page')
        raise AuthenticationError(
          format_auth_error(
            'authenticate with Zwiftpower',
            login_url_from_form,
            Exception('Authentication failed'),
            suggestion='Your username or password is incorrect. Verify your credentials.',
          ),
        )
      logger.info('Successfully authenticated with Zwiftpower')
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error during authentication: {e}')
      raise NetworkError(
        format_network_error(
          'authenticate with Zwiftpower',
          login_url_from_form,
          e,
          status_code=e.response.status_code,
        ),
      ) from e
    except httpx.RequestError as e:
      logger.error(f'Network error during authentication: {e}')
      raise NetworkError(
        format_network_error(
          'authenticate with Zwiftpower',
          login_url_from_form,
          e,
        ),
      ) from e

  # ----------------------------------------------------------------------------
  async def _create_client(self) -> httpx.AsyncClient:
    """Create and configure an async HTTP client.

    SECURITY: All connections use HTTPS with certificate verification enabled.
    This protects against man-in-the-middle attacks.

    Returns:
      Configured httpx.AsyncClient instance
    """
    logger.debug(
      'Creating new httpx async client with HTTPS certificate verification',
    )
    # SECURITY: Explicitly enable certificate verification for HTTPS
    return httpx.AsyncClient(follow_redirects=True, verify=True)

  # ----------------------------------------------------------------------------
  async def _before_request(
    self,
    url: str,
    method: str = 'GET',
    **kwargs: Any,
  ) -> None:
    """Ensure logged in before making requests."""
    if not self._client:
      await self.login()

  # ----------------------------------------------------------------------------
  def login_url(self, url: str | None = None) -> str:
    """Get or set the login URL.

    Args:
      url: Optional new login URL to set. If None, returns current URL.

    Returns:
      The current login URL (after updating if url was provided)
    """
    if url:
      self._login_url = url

    return self._login_url

  # ----------------------------------------------------------------------------
  async def fetch_json(
    self,
    endpoint: str,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
  ) -> str:
    """Fetch JSON data from a Zwiftpower endpoint and return as raw string (async).

    Automatically logs in if not already authenticated. Retries on transient
    network errors.

    Args:
      endpoint: Full URL of the JSON endpoint to fetch
      max_retries: Maximum number of retry attempts for transient errors
      backoff_factor: Multiplier for exponential backoff delays (default: 1.0)

    Returns:
      Raw JSON response as a string

    Raises:
      NetworkError: If the HTTP request fails after retries
    """
    try:
      logger.debug(f'Fetching JSON from: {endpoint}')
      if not self._client:
        await self.init_client()
      assert self._client is not None
      pres = await fetch_with_retry_async(
        self._client,
        endpoint,
        method='GET',
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        logger=logger,
      )

      res = pres.text
      logger.debug(f'Successfully fetched raw JSON from {endpoint}')
      return res
    except NetworkError:
      raise
    except httpx.HTTPStatusError as e:
      logger.debug(f'HTTP error fetching {endpoint}: {e}')
      # Special handling for 403 on cyclist profile URLs
      if e.response.status_code == 403 and 'zwiftpower.com/cache3/profile/' in endpoint:
        raise NetworkError(
          format_network_error(
            'fetch Zwift profile',
            endpoint,
            e,
            status_code=e.response.status_code,
          ),
        ) from e
      raise NetworkError(
        format_network_error(
          'fetch JSON data',
          endpoint,
          e,
          status_code=e.response.status_code,
        ),
      ) from e
    except httpx.RequestError as e:
      logger.error(f'Network error fetching {endpoint}: {e}')
      raise NetworkError(
        format_network_error('fetch JSON data', endpoint, e),
      ) from e

  # ----------------------------------------------------------------------------
  async def fetch_page(
    self,
    endpoint: str,
    max_retries: int = 3,
  ) -> str:
    """Fetch HTML page content from a Zwiftpower endpoint (async).

    Automatically logs in if not already authenticated. Retries on transient
    network errors.

    Args:
      endpoint: Full URL of the page to fetch
      max_retries: Maximum number of retry attempts for transient errors

    Returns:
      String containing the HTML page content

    Raises:
      NetworkError: If the HTTP request fails after retries
    """
    try:
      logger.debug(f'Fetching HTML page from: {endpoint}')
      if not self._client:
        await self.init_client()
      assert self._client is not None
      pres = await fetch_with_retry_async(
        self._client,
        endpoint,
        method='GET',
        max_retries=max_retries,
        logger=logger,
      )
      logger.debug(f'Successfully fetched HTML from {endpoint}')
      return pres.text
    except NetworkError:
      raise
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error fetching {endpoint}: {e}')
      raise NetworkError(
        format_network_error(
          'fetch page',
          endpoint,
          e,
          status_code=e.response.status_code,
        ),
      ) from e
    except httpx.RequestError as e:
      logger.error(f'Network error fetching {endpoint}: {e}')
      raise NetworkError(
        format_network_error('fetch page', endpoint, e),
      ) from e

  # ----------------------------------------------------------------------------
  async def _on_close(self) -> None:
    """Hook called when closing - clear credentials."""
    self.clear_credentials()

  # ----------------------------------------------------------------------------
  async def close(self) -> None:
    """Compatibility wrapper for aclose() to match test expectations."""
    await self.aclose()

  # ----------------------------------------------------------------------------
  async def _fetch_with_retry(
    self,
    url: str,
    method: str = 'GET',
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    **kwargs: Any,
  ) -> httpx.Response:
    """Compatibility wrapper for fetch_with_retry_async.

    Deprecated: Use fetch_with_retry_async() directly. This method exists
    only for backward compatibility with existing tests.
    """
    if not self._client:
      await self.login()
    assert self._client is not None
    return await fetch_with_retry_async(
      self._client,
      url,
      method=method,
      max_retries=max_retries,
      backoff_factor=backoff_factor,
      logger=logger,
    )

  # ----------------------------------------------------------------------------
  @staticmethod
  def set_pen(label: int) -> str:
    """Convert penalty label to string representation.

    Args:
      label: Penalty label integer

    Returns:
      String representation of the penalty
    """
    penalties = {
      0: 'none',
      10: 'time',
      20: 'upgrade',
      30: 'DSQ',
      40: 'DSQ',
    }
    return penalties.get(label, 'unknown')

  # ----------------------------------------------------------------------------
  @staticmethod
  def set_rider_category(div: int) -> str:
    """Convert division number to rider category.

    Args:
      div: Division number

    Returns:
      Category letter (A, B, C, D, E)
    """
    categories = {
      10: 'A',
      20: 'B',
      30: 'C',
      40: 'D',
      50: 'E',
    }
    return categories.get(div, 'unknown')

  # ----------------------------------------------------------------------------
  @staticmethod
  def set_category(div: int) -> str:
    """Convert division number to category name.

    Args:
      div: Division number

    Returns:
      Category name string
    """
    categories = {
      10: 'A',
      20: 'B',
      30: 'C',
      40: 'D',
      50: 'E',
    }
    return categories.get(div, 'unknown')
