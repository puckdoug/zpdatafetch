import json
import sys
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup

from zpdatafetch.config import Config


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

  Attributes:
    verbose: Enable verbose output for debugging
    username: Zwiftpower username loaded from keyring
    password: Zwiftpower password loaded from keyring
    login_response: Response from the login POST request
  """

  _client: httpx.Client | None = None
  _login_url: str = (
    'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
  )
  verbose: bool = False

  # -------------------------------------------------------------------------------
  def __init__(self, skip_credential_check: bool = False) -> None:
    """Initialize the ZP client with credentials from keyring.

    Args:
      skip_credential_check: Skip validation of credentials (used for testing)

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

  # -------------------------------------------------------------------------------
  def login(self) -> None:
    """Authenticate with Zwiftpower and establish a session.

    Fetches the login page, extracts the login form URL, and submits
    credentials to authenticate. Sets login_response with the result.

    Raises:
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If login form cannot be parsed or auth fails
    """
    if self.verbose:
      print('Logging in to Zwiftpower')

    if not self._client:
      self.init_client()

    try:
      if self.verbose:
        print(f'Fetching url: {self._login_url}')
      page = self._client.get(self._login_url)
      page.raise_for_status()
    except httpx.HTTPStatusError as e:
      raise ZPNetworkError(f'Failed to fetch login page: {e}') from e
    except httpx.RequestError as e:
      raise ZPNetworkError(f'Network error during login: {e}') from e

    self._client.cookies.get('phpbb3_lswlk_sid')

    try:
      soup = BeautifulSoup(page.text, 'lxml')
      if not soup.form or 'action' not in soup.form.attrs:
        raise ZPAuthenticationError(
          'Login form not found on page. Zwiftpower may have changed their login flow.',
        )
      login_url_from_form = soup.form['action'][0:]
    except (AttributeError, KeyError) as e:
      raise ZPAuthenticationError(f'Could not parse login form: {e}') from e

    data = {'username': self.username, 'password': self.password}
    if self.verbose:
      print(f'Posting to url: {login_url_from_form}')

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
        raise ZPAuthenticationError(
          'Login failed. Please check your username and password.',
        )
    except httpx.HTTPStatusError as e:
      raise ZPNetworkError(f'HTTP error during authentication: {e}') from e
    except httpx.RequestError as e:
      raise ZPNetworkError(f'Network error during authentication: {e}') from e

  # -------------------------------------------------------------------------------
  def init_client(self, client: httpx.Client | None = None) -> None:
    """Initialize or replace the HTTP client.

    Allows a custom httpx.Client to be injected, useful for testing
    with mocked HTTP transports.

    Args:
      client: Optional httpx.Client instance to use. If None, creates a
        new client with redirect following enabled.
    """
    if self.verbose:
      print('Initialzing httpx client')

    if client:
      self._client = client
    else:
      self._client = httpx.Client(follow_redirects=True)

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
  def fetch_json(self, endpoint: str) -> dict[str, Any]:
    """Fetch JSON data from a Zwiftpower endpoint.

    Automatically logs in if not already authenticated. Returns an empty
    dict if the response cannot be decoded as JSON.

    Args:
      endpoint: Full URL of the JSON endpoint to fetch

    Returns:
      Dictionary containing the parsed JSON response, or empty dict if
      JSON decoding fails

    Raises:
      ZPNetworkError: If the HTTP request fails
    """
    if self._client is None:
      self.login()

    try:
      if self.verbose:
        print(f'Fetching: {endpoint}')
      pres = self._client.get(endpoint, cookies=self._client.cookies)
      pres.raise_for_status()

      try:
        res = pres.json()
      except json.decoder.JSONDecodeError:
        if self.verbose:
          print(f'Warning: Could not decode JSON from {endpoint}, returning empty dict')
        res = {}
      return res
    except httpx.HTTPStatusError as e:
      raise ZPNetworkError(f'HTTP error fetching {endpoint}: {e}') from e
    except httpx.RequestError as e:
      raise ZPNetworkError(f'Network error fetching {endpoint}: {e}') from e

  # -------------------------------------------------------------------------------
  def fetch_page(self, endpoint: str) -> str:
    """Fetch HTML page content from a Zwiftpower endpoint.

    Automatically logs in if not already authenticated.

    Args:
      endpoint: Full URL of the page to fetch

    Returns:
      String containing the HTML page content

    Raises:
      ZPNetworkError: If the HTTP request fails
    """
    if self._client is None:
      self.login()

    try:
      if self.verbose:
        print(f'Fetching: {endpoint}')

      pres = self._client.get(endpoint, cookies=self._client.cookies)
      pres.raise_for_status()
      res = pres.text
      return res
    except httpx.HTTPStatusError as e:
      raise ZPNetworkError(f'HTTP error fetching {endpoint}: {e}') from e
    except httpx.RequestError as e:
      raise ZPNetworkError(f'Network error fetching {endpoint}: {e}') from e

  # -------------------------------------------------------------------------------
  def close(self) -> None:
    """Close the HTTP client and clean up resources."""
    if self._client:
      try:
        self._client.close()
      except Exception as e:
        if self.verbose:
          sys.stderr.write(f'Could not close client properly: {e}\n')

  # -------------------------------------------------------------------------------
  def __del__(self) -> None:
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
