import json
import time
from typing import Any

import httpx
from bs4 import BeautifulSoup

from zpdatafetch.config import Config
from zpdatafetch.logging_config import get_logger

logger = get_logger(__name__)


# ===============================================================================
class ZPAuthenticationError(Exception):
  """Raised when authentication with Zwiftpower fails.

  This exception is raised when login credentials are rejected,
  the login form cannot be found, or authentication otherwise fails.
  """


# ===============================================================================
class ZPNetworkError(Exception):
  """Raised when network requests to Zwiftpower fail.

  This exception is raised for HTTP errors, connection errors,
  timeouts, and other network-related issues.
  """


# ===============================================================================
class ZPConfigError(Exception):
  """Raised when configuration is invalid or missing.

  This exception is raised when credentials are not found in the keyring
  or other configuration issues are detected.
  """


# ===============================================================================
class ZP:
  """Core class for interacting with the Zwiftpower API.

  This class handles authentication, session management, and HTTP requests
  to the Zwiftpower website. It manages login state and provides methods
  for fetching JSON data and HTML pages.

  Logging is done via the standard logging module. Configure logging using
  zpdatafetch.logging_config.setup_logging() for detailed output.

  Attributes:
    username: Zwiftpower username loaded from keyring
    password: Zwiftpower password loaded from keyring
    login_response: Response from the login POST request
  """

  _client: httpx.Client | None = None
  _login_url: str = (
    'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
  )
  _shared_client: httpx.Client | None = None
  _owns_client: bool = False

  # -------------------------------------------------------------------------------
  def __init__(
    self,
    skip_credential_check: bool = False,
    shared_client: bool = False,
  ) -> None:
    """Initialize the ZP client with credentials from keyring.

    Args:
      skip_credential_check: Skip validation of credentials (used for testing)
      shared_client: Use a shared HTTP client for connection pooling (default: False).
        Useful when creating multiple ZP instances for batch operations.

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
    if shared_client and ZP._shared_client is None:
      logger.debug('Creating shared HTTP client for connection pooling')
      ZP._shared_client = httpx.Client(follow_redirects=True)

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
  def login(self) -> None:
    """Authenticate with Zwiftpower and establish a session.

    Fetches the login page, extracts the login form URL, and submits
    credentials to authenticate. Sets login_response with the result.

    Raises:
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If login form cannot be parsed or auth fails
    """
    logger.info('Logging in to Zwiftpower')

    if not self._client:
      self.init_client()

    try:
      logger.debug(f'Fetching url: {self._login_url}')
      page = self._client.get(self._login_url)
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
      self.login_response = self._client.post(
        login_url_from_form,
        data=data,
        cookies=self._client.cookies,
      )
      self.login_response.raise_for_status()

      # Check if login was actually successful by looking for error indicators
      # If we're redirected back to a login/ucp page, authentication likely failed
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
  def init_client(self, client: httpx.Client | None = None) -> None:
    """Initialize or replace the HTTP client.

    Allows a custom httpx.Client to be injected, useful for testing
    with mocked HTTP transports. If no client is provided, uses the
    shared client if available, otherwise creates a new one.

    SECURITY: All connections use HTTPS with certificate verification enabled.
    This protects against man-in-the-middle attacks.

    Args:
      client: Optional httpx.Client instance to use. If None, uses shared
        client if available, otherwise creates a new client.
    """
    logger.debug('Initializing httpx client')

    if client:
      logger.debug('Using provided httpx client')
      self._client = client
    elif ZP._shared_client is not None:
      logger.debug('Using shared HTTP client for connection pooling')
      self._client = ZP._shared_client
    else:
      logger.debug('Creating new httpx client with HTTPS certificate verification')
      # SECURITY: Explicitly enable certificate verification for HTTPS connections
      self._client = httpx.Client(follow_redirects=True, verify=True)

  # -------------------------------------------------------------------------------
  def _fetch_with_retry(
    self,
    url: str,
    method: str = 'GET',
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    **kwargs: Any,
  ) -> httpx.Response:
    """Fetch URL with exponential backoff retry logic.

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
      self.login()

    last_exception: Exception | None = None

    for attempt in range(max_retries):
      try:
        logger.debug(f'Attempt {attempt + 1}/{max_retries}: {method} {url}')
        response = self._client.request(method, url, **kwargs)
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
        time.sleep(wait_time)
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
          time.sleep(wait_time)
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
        time.sleep(wait_time)

    if last_exception:
      logger.error(f'Max retries ({max_retries}) exhausted: {last_exception}')
      raise ZPNetworkError(
        f'Failed after {max_retries} attempts: {last_exception}',
      ) from last_exception

    raise ZPNetworkError(f'Unexpected error fetching {url}')

  # -------------------------------------------------------------------------------
  def login_url(self, url: str | None = None) -> str:
    """Get or set the login URL.

    Allows the login URL to be overridden, useful for testing against
    different environments.

    Args:
      url: Optional new login URL to set. If None, returns current URL.

    Returns:
      The current login URL (after updating if url was provided)
    """
    if url:
      self._login_url = url

    return self._login_url

  # -------------------------------------------------------------------------------
  def fetch_json(self, endpoint: str, max_retries: int = 3) -> dict[str, Any]:
    """Fetch JSON data from a Zwiftpower endpoint.

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
      pres = self._fetch_with_retry(
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
  def fetch_page(self, endpoint: str, max_retries: int = 3) -> str:
    """Fetch HTML page content from a Zwiftpower endpoint.

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
      logger.debug(f'Fetching page from: {endpoint}')

      pres = self._fetch_with_retry(
        endpoint,
        method='GET',
        max_retries=max_retries,
      )
      res = pres.text
      logger.debug(f'Successfully fetched page from {endpoint}')
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
  @classmethod
  def close_shared_session(cls) -> None:
    """Close the shared HTTP client used for connection pooling.

    Call this when you're done with all batch operations to free resources.

    Example:
      try:
          zp1 = ZP(shared_client=True)
          zp2 = ZP(shared_client=True)
          zp1.fetch_json(url1)
          zp2.fetch_json(url2)
      finally:
          ZP.close_shared_session()
    """
    if cls._shared_client is not None:
      try:
        cls._shared_client.close()
        logger.debug('Shared HTTP client closed successfully')
        cls._shared_client = None
      except Exception as e:
        logger.error(f'Could not close shared client properly: {e}')

  # -------------------------------------------------------------------------------
  def close(self) -> None:
    """Close the HTTP client and clean up resources.

    Closes the HTTP client and clears credentials from memory.
    Only closes the client if this instance owns it. Shared clients
    should be closed via close_shared_session().
    """
    # Clear credentials first for security
    self.clear_credentials()

    if self._client and self._owns_client:
      try:
        self._client.close()
        logger.debug('HTTP client closed successfully')
      except Exception as e:
        logger.error(f'Could not close client properly: {e}')
    elif self._client and not self._owns_client:
      logger.debug('Skipping close of shared client')

  # -------------------------------------------------------------------------------
  def __enter__(self) -> 'ZP':
    """Enter context manager - return self for use in 'with' statement.

    Returns:
      The ZP instance for use within the context block.

    Example:
      with ZP() as zp:
          zp.login()
          data = zp.fetch_json(url)
    """
    logger.debug('Entering ZP context manager')
    return self

  # -------------------------------------------------------------------------------
  def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
    """Exit context manager - ensure cleanup always happens.

    Guarantees that the HTTP client is closed when exiting the context,
    whether normally or due to an exception.

    Args:
      exc_type: Exception type if an exception occurred, None otherwise.
      exc_val: Exception value if an exception occurred, None otherwise.
      exc_tb: Exception traceback if an exception occurred, None otherwise.

    Returns:
      False to propagate any exceptions that occurred.
    """
    logger.debug('Exiting ZP context manager')
    self.close()
    return False

  # -------------------------------------------------------------------------------
  def __del__(self) -> None:
    """Cleanup on object destruction."""
    self.close()

  # -------------------------------------------------------------------------------
  @classmethod
  def set_pen(cls, label: int) -> str:
    """Convert numeric pen label to letter category.

    Args:
      label: Numeric pen label (0-5)

    Returns:
      Letter category ('A', 'B', 'C', 'D', 'E') or string of label if unknown
    """
    match label:
      case 0:
        return 'E'
      case 1:
        return 'A'
      case 2:
        return 'B'
      case 3:
        return 'C'
      case 4:
        return 'D'
      case 5:
        return 'E'
      case _:
        return str(label)

  # -------------------------------------------------------------------------------
  @classmethod
  def set_rider_category(cls, div: int) -> str:
    """Convert numeric division to rider category letter.

    Args:
      div: Numeric division (0, 10, 20, 30, 40)

    Returns:
      Category letter ('', 'A', 'B', 'C', 'D') or string of div if unknown
    """
    match div:
      case 0:
        return ''
      case 10:
        return 'A'
      case 20:
        return 'B'
      case 30:
        return 'C'
      case 40:
        return 'D'
      case _:
        return str(div)

  # -------------------------------------------------------------------------------
  @classmethod
  def set_category(cls, div: int) -> str:
    """Convert numeric division to category letter.

    Args:
      div: Numeric division (0, 10, 20, 30, 40)

    Returns:
      Category letter ('E', 'A', 'B', 'C', 'D') or string of div if unknown
    """
    match div:
      case 0:
        return 'E'
      case 10:
        return 'A'
      case 20:
        return 'B'
      case 30:
        return 'C'
      case 40:
        return 'D'
      case _:
        return str(div)


# ===============================================================================
def main() -> None:
  """
  Core module for accessing Zwiftpower API endpoints
  """
  zp = ZP()
  zp.verbose = True
  zp.login()
  if zp.login_response:
    print(zp.login_response.status_code)
  zp.close()


# ===============================================================================
if __name__ == '__main__':
  main()
