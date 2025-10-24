import json
import sys
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup

from zpdatafetch.config import Config


# ===============================================================================
class ZPAuthenticationError(Exception):
  """Raised when authentication with Zwiftpower fails"""


# ===============================================================================
class ZPNetworkError(Exception):
  """Raised when network requests to Zwiftpower fail"""


# ===============================================================================
class ZPConfigError(Exception):
  """Raised when configuration is invalid or missing"""


# ===============================================================================
class ZP:
  _client: httpx.Client | None = None
  _login_url: str = (
    'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
  )
  verbose: bool = False

  # -------------------------------------------------------------------------------
  def __init__(self, skip_credential_check: bool = False) -> None:
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
    """
    Allow another client to be substituted for fetching web pages e.g. to allow
    testing with httpx_mock.
    """
    if self.verbose:
      print('Initialzing httpx client')

    if client:
      self._client = client
    else:
      self._client = httpx.Client(follow_redirects=True)

  # -------------------------------------------------------------------------------
  def login_url(self, url: str | None = None) -> str:
    """
    Allow the login URL to be overridden. With no arguments it returns the current
    URL. With arguments it will update the URL and return the new value.
    """
    if url:
      self._login_url = url

    return self._login_url

  # -------------------------------------------------------------------------------
  def fetch_json(self, endpoint: str) -> dict[str, Any]:
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
