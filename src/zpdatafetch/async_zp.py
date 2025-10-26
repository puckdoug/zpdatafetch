"""Async version of the ZP class for asynchronous Zwiftpower API access.

This module provides async/await compatible interfaces for the Zwiftpower API,
allowing for concurrent requests and better performance in async applications.
"""

import json
from typing import Any

import anyio
import httpx
from bs4 import BeautifulSoup

from zpdatafetch.config import Config
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZPAuthenticationError, ZPConfigError, ZPNetworkError

logger = get_logger(__name__)


# ===============================================================================
class AsyncZP:
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

  # -------------------------------------------------------------------------------
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
      ZPConfigError: If credentials are not found in keyring
    """
    self.config: Config = Config()
    self.config.load()
    self.username: str = self.config.username
    self.password: str = self.config.password
    self.login_response: httpx.Response | None = None

    if not skip_credential_check and (not self.username or not self.password):
      raise ZPConfigError(
        'Zwiftpower credentials not found. Please run "zpdata config" to set up your credentials.',
      )

    self._owns_client = not shared_client
    if shared_client and AsyncZP._shared_client is None:
      logger.debug('Creating shared async HTTP client for connection pooling')
      AsyncZP._shared_client = httpx.AsyncClient(follow_redirects=True)

  # -------------------------------------------------------------------------------
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

  # -------------------------------------------------------------------------------
  async def login(self) -> None:
    """Authenticate with Zwiftpower and establish an async session.

    Fetches the login page, extracts the login form URL, and submits
    credentials to authenticate. Sets login_response with the result.

    Raises:
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If login form cannot be parsed or auth fails
    """
    logger.info('Logging in to Zwiftpower (async)')

    if not self._client:
      await self.init_client()

    try:
      logger.debug(f'Fetching url: {self._login_url}')
      page = await self._client.get(self._login_url)
      page.raise_for_status()
    except httpx.HTTPStatusError as e:
      logger.error(f'Failed to fetch login page: {e}')
      raise ZPNetworkError(f'Failed to fetch login page: {e}') from e
    except httpx.RequestError as e:
      logger.error(f'Network error during login: {e}')
      raise ZPNetworkError(f'Network error during login: {e}') from e

    self._client.cookies.get('phpbb3_lswlk_sid')

    try:
      soup = BeautifulSoup(page.text, 'lxml')
      if not soup.form or 'action' not in soup.form.attrs:
        logger.error('Login form not found on page')
        raise ZPAuthenticationError(
          'Login form not found on page. Zwiftpower may have changed their login flow.',
        )
      login_url_from_form = soup.form['action'][0:]
      logger.debug(f'Extracted login form URL: {login_url_from_form}')
    except (AttributeError, KeyError) as e:
      logger.error(f'Could not parse login form: {e}')
      raise ZPAuthenticationError(f'Could not parse login form: {e}') from e

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
        raise ZPAuthenticationError(
          'Login failed. Please check your username and password.',
        )
      logger.info('Successfully authenticated with Zwiftpower')
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error during authentication: {e}')
      raise ZPNetworkError(f'HTTP error during authentication: {e}') from e
    except httpx.RequestError as e:
      logger.error(f'Network error during authentication: {e}')
      raise ZPNetworkError(f'Network error during authentication: {e}') from e

  # -------------------------------------------------------------------------------
  async def init_client(
    self,
    client: httpx.AsyncClient | None = None,
  ) -> None:
    """Initialize or replace the async HTTP client.

    Args:
      client: Optional httpx.AsyncClient instance to use. If None, uses shared
        client if available, otherwise creates a new client.
    """
    logger.debug('Initializing httpx async client')

    if client:
      logger.debug('Using provided httpx async client')
      self._client = client
    elif AsyncZP._shared_client is not None:
      logger.debug('Using shared async HTTP client for connection pooling')
      self._client = AsyncZP._shared_client
    else:
      logger.debug(
        'Creating new httpx async client with HTTPS certificate verification',
      )
      # SECURITY: Explicitly enable certificate verification for HTTPS
      self._client = httpx.AsyncClient(follow_redirects=True, verify=True)

  # -------------------------------------------------------------------------------
  async def _fetch_with_retry(
    self,
    url: str,
    method: str = 'GET',
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    **kwargs: Any,
  ) -> httpx.Response:
    """Fetch URL with exponential backoff retry logic (async).

    Retries on transient errors (connection errors, timeouts) but not on
    client errors (4xx) or authentication errors.

    Args:
      url: URL to fetch
      method: HTTP method (default: 'GET')
      max_retries: Maximum number of retry attempts (default: 3)
      backoff_factor: Multiplier for exponential backoff (default: 1.0)
      **kwargs: Additional arguments to pass to httpx client method

    Returns:
      httpx.Response: The successful response

    Raises:
      ZPNetworkError: If all retries are exhausted
    """
    if self._client is None:
      await self.login()

    last_exception: Exception | None = None

    for attempt in range(max_retries):
      try:
        logger.debug(f'Attempt {attempt + 1}/{max_retries}: {method} {url}')
        response = await self._client.request(method, url, **kwargs)
        response.raise_for_status()
        return response
      except (httpx.ConnectError, httpx.TimeoutException) as e:
        last_exception = e
        if attempt == max_retries - 1:
          break
        wait_time = backoff_factor * (2**attempt)
        logger.warning(
          f'Transient network error on attempt {attempt + 1}: {e}. '
          f'Retrying in {wait_time:.1f}s...',
        )
        await anyio.sleep(wait_time)
      except httpx.HTTPStatusError as e:
        if 500 <= e.response.status_code < 600:
          last_exception = e
          if attempt == max_retries - 1:
            break
          wait_time = backoff_factor * (2**attempt)
          logger.warning(
            f'Server error ({e.response.status_code}) on attempt '
            f'{attempt + 1}: {e}. Retrying in {wait_time:.1f}s...',
          )
          await anyio.sleep(wait_time)
        else:
          raise ZPNetworkError(f'HTTP error: {e}') from e
      except httpx.RequestError as e:
        last_exception = e
        if attempt == max_retries - 1:
          break
        wait_time = backoff_factor * (2**attempt)
        logger.warning(
          f'Request error on attempt {attempt + 1}: {e}. '
          f'Retrying in {wait_time:.1f}s...',
        )
        await anyio.sleep(wait_time)

    if last_exception:
      logger.error(f'Max retries ({max_retries}) exhausted: {last_exception}')
      raise ZPNetworkError(
        f'Failed after {max_retries} attempts: {last_exception}',
      ) from last_exception

    raise ZPNetworkError(f'Unexpected error fetching {url}')

  # -------------------------------------------------------------------------------
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

  # -------------------------------------------------------------------------------
  async def fetch_json(
    self,
    endpoint: str,
    max_retries: int = 3,
  ) -> dict[str, Any]:
    """Fetch JSON data from a Zwiftpower endpoint (async).

    Automatically logs in if not already authenticated. Retries on transient
    network errors. Returns an empty dict if the response cannot be decoded
    as JSON.

    Args:
      endpoint: Full URL of the JSON endpoint to fetch
      max_retries: Maximum number of retry attempts for transient errors

    Returns:
      Dictionary containing the parsed JSON response, or empty dict if
      JSON decoding fails

    Raises:
      ZPNetworkError: If the HTTP request fails after retries
    """
    try:
      logger.debug(f'Fetching JSON from: {endpoint}')
      pres = await self._fetch_with_retry(
        endpoint,
        method='GET',
        max_retries=max_retries,
      )

      try:
        res = pres.json()
        logger.debug(f'Successfully fetched and parsed JSON from {endpoint}')
      except json.decoder.JSONDecodeError:
        logger.warning(
          f'Could not decode JSON from {endpoint}, returning empty dict',
        )
        res = {}
      return res
    except ZPNetworkError:
      raise
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error fetching {endpoint}: {e}')
      raise ZPNetworkError(f'HTTP error fetching {endpoint}: {e}') from e
    except httpx.RequestError as e:
      logger.error(f'Network error fetching {endpoint}: {e}')
      raise ZPNetworkError(f'Network error fetching {endpoint}: {e}') from e

  # -------------------------------------------------------------------------------
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
      ZPNetworkError: If the HTTP request fails after retries
    """
    try:
      logger.debug(f'Fetching HTML page from: {endpoint}')
      pres = await self._fetch_with_retry(
        endpoint,
        method='GET',
        max_retries=max_retries,
      )
      logger.debug(f'Successfully fetched HTML from {endpoint}')
      return pres.text
    except ZPNetworkError:
      raise
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error fetching {endpoint}: {e}')
      raise ZPNetworkError(f'HTTP error fetching {endpoint}: {e}') from e
    except httpx.RequestError as e:
      logger.error(f'Network error fetching {endpoint}: {e}')
      raise ZPNetworkError(f'Network error fetching {endpoint}: {e}') from e

  # -------------------------------------------------------------------------------
  @classmethod
  async def close_shared_session(cls) -> None:
    """Close the shared async client if it exists.

    This should be called when your application is shutting down to ensure
    the shared connection pool is properly closed. Only needed if you used
    shared_client=True when creating instances.

    Example:
      await AsyncZP.close_shared_session()
    """
    if cls._shared_client:
      logger.debug('Closing shared async HTTP client')
      await cls._shared_client.aclose()
      cls._shared_client = None
      logger.debug('Shared async client closed')

  # -------------------------------------------------------------------------------
  async def close(self) -> None:
    """Close the HTTP client and clean up resources.

    This method should be called when you're done with the AsyncZP instance
    to ensure proper cleanup of network resources.
    """
    if self._client and self._owns_client:
      try:
        await self._client.aclose()
        logger.debug('Async HTTP client closed successfully')
      except Exception as e:
        logger.error(f'Could not close async client properly: {e}')

  # -------------------------------------------------------------------------------
  async def __aenter__(self) -> 'AsyncZP':
    """Enter async context manager - return self for use in 'async with' statement."""
    return self

  # -------------------------------------------------------------------------------
  async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
    """Exit async context manager - ensure cleanup always happens.

    Args:
      exc_type: Exception type if an exception occurred
      exc_val: Exception value if an exception occurred
      exc_tb: Exception traceback if an exception occurred

    Returns:
      False to propagate any exceptions that occurred
    """
    await self.close()
    return False

  # -------------------------------------------------------------------------------
  def __del__(self) -> None:
    """Fallback cleanup if context manager not used.

    Note: This uses a synchronous close which may not work properly
    for async clients. Always prefer using async with or explicitly
    calling await close().
    """
    # We can't call async close() from __del__, so just log a warning
    if self._client and self._owns_client:
      logger.warning(
        'AsyncZP instance deleted without proper cleanup. '
        'Use "async with AsyncZP()" or call "await zp.close()" explicitly.',
      )

  # -------------------------------------------------------------------------------
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

  # -------------------------------------------------------------------------------
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

  # -------------------------------------------------------------------------------
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
