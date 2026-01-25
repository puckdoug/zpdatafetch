from typing import Any

import httpx
from bs4 import BeautifulSoup

from shared.error_helpers import format_auth_error, format_network_error
from shared.exceptions import AuthenticationError, ConfigError, NetworkError
from shared.http_client import BaseHTTPClient, fetch_with_retry_sync
from zpdatafetch.config import Config
from zpdatafetch.logging_config import get_logger

logger = get_logger(__name__)


# ==============================================================================
class ZP(BaseHTTPClient):
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

  # ----------------------------------------------------------------------------
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
    if shared_client and ZP._shared_client is None:
      logger.debug('Creating shared HTTP client for connection pooling')
      ZP._shared_client = self._create_client()

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
  def login(self) -> None:
    """Authenticate with Zwiftpower and establish a session.

    Fetches the login page, extracts the login form URL, and submits
    credentials to authenticate. Sets login_response with the result.

    Raises:
      NetworkError: If network requests fail
      AuthenticationError: If login form cannot be parsed or auth fails
    """
    logger.info('Logging in to Zwiftpower')

    if not self._client:
      self.init_client()
    assert self._client is not None

    try:
      logger.debug(f'Fetching url: {self._login_url}')
      page = self._client.get(self._login_url)
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
  def _create_client(self) -> httpx.Client:
    """Create and configure an HTTP client.

    SECURITY: All connections use HTTPS with certificate verification enabled.
    This protects against man-in-the-middle attacks.

    Returns:
      Configured httpx.Client instance
    """
    logger.debug(
      'Creating new httpx client with HTTPS certificate verification',
    )
    # SECURITY: Explicitly enable certificate verification for HTTPS connections
    return httpx.Client(follow_redirects=True, verify=True)

  # ----------------------------------------------------------------------------
  def _before_request(
    self,
    url: str,
    method: str = 'GET',
    **kwargs: Any,
  ) -> None:
    """Ensure logged in before making requests."""
    if not self._client:
      self.login()

  # ----------------------------------------------------------------------------
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

  # ----------------------------------------------------------------------------
  def fetch_json(self, endpoint: str, max_retries: int = 3) -> str:
    """Fetch JSON data from a Zwiftpower endpoint and return as raw string.

    Automatically logs in if not already authenticated. Retries on transient
    network errors.

    Args:
      endpoint: Full URL of the JSON endpoint to fetch
      max_retries: Maximum number of retry attempts for transient errors

    Returns:
      Raw JSON response as a string

    Raises:
      NetworkError: If the HTTP request fails after retries
    """
    try:
      logger.debug(f'Fetching JSON from: {endpoint}')
      if not self._client:
        self.init_client()
      assert self._client is not None
      pres = fetch_with_retry_sync(
        self._client,
        endpoint,
        method='GET',
        max_retries=max_retries,
        logger=logger,
      )

      res = pres.text
      logger.debug(f'Successfully fetched raw JSON from {endpoint}')
      return res
    except NetworkError:
      raise
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error fetching {endpoint}: {e}')
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
      NetworkError: If the HTTP request fails after retries
    """
    try:
      logger.debug(f'Fetching page from: {endpoint}')

      if not self._client:
        self.init_client()
      assert self._client is not None
      pres = fetch_with_retry_sync(
        self._client,
        endpoint,
        method='GET',
        max_retries=max_retries,
        logger=logger,
      )
      res = pres.text
      logger.debug(f'Successfully fetched page from {endpoint}')
      return res
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

  # ----------------------------------------------------------------------------
  def _on_close(self) -> None:
    """Hook called when closing - clear credentials."""
    self.clear_credentials()

  # ----------------------------------------------------------------------------
  def _fetch_with_retry(
    self,
    url: str,
    method: str = 'GET',
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    **kwargs: Any,
  ) -> httpx.Response:
    """Compatibility wrapper for fetch_with_retry_sync.

    Deprecated: Use fetch_with_retry_sync() directly. This method exists
    only for backward compatibility with existing tests.
    """
    if not self._client:
      self.login()
    assert self._client is not None
    return fetch_with_retry_sync(
      self._client,
      url,
      method=method,
      max_retries=max_retries,
      backoff_factor=backoff_factor,
      logger=logger,
    )

  # ----------------------------------------------------------------------------
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

  # ----------------------------------------------------------------------------
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

  # ----------------------------------------------------------------------------
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


# ==============================================================================
def main() -> None:
  """
  Core module for accessing Zwiftpower API endpoints
  """
  zp = ZP()
  zp.verbose = True  # type: ignore[attr-defined]
  zp.login()
  if zp.login_response:
    print(zp.login_response.status_code)
  zp.close()


# ==============================================================================
if __name__ == '__main__':
  main()
