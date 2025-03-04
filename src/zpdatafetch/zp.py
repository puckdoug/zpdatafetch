import json
import sys

import httpx
from bs4 import BeautifulSoup

from zpdatafetch.config import Config


# ===============================================================================
class ZP:
  _client: httpx.Client = None
  _login_url: str = (
    'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
  )
  verbose: bool = False

  # -------------------------------------------------------------------------------
  def __init__(self):
    self.config = Config()
    self.config.load()
    self.username = self.config.username
    self.password = self.config.password

  # -------------------------------------------------------------------------------
  def login(self):
    if self.verbose:
      print('Logging in to Zwiftpower')

    if not self._client:
      self.init_client()

    if self.verbose:
      print(f'Fetching url: {self._login_url}')
    page = self._client.get(self._login_url)

    self._client.cookies.get('phpbb3_lswlk_sid')
    soup = BeautifulSoup(page.text, 'lxml')
    login_url_from_form = soup.form['action'][0:]
    data = {'username': self.username, 'password': self.password}
    if self.verbose:
      print(f'Posting to url: {login_url_from_form}')

    self.login = self._client.post(
      login_url_from_form,
      data=data,
      cookies=self._client.cookies,
    )

  # -------------------------------------------------------------------------------
  def init_client(self, client=None):
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
  def login_url(self, url=None):
    """
    Allow the login URL to be overridden. With no arguments it returns the current
    URL. With arguments it will update the URL and return the new value.
    """
    if url:
      self._login_url = url

    return self._login_url

  # -------------------------------------------------------------------------------
  def fetch_json(self, endpoint):
    if self._client is None:
      self.login()

    if self.verbose:
      print(f'Fetching: {endpoint}')
    pres = self._client.get(endpoint, cookies=self._client.cookies)
    try:
      res = pres.json()
    except json.decoder.JSONDecodeError:
      res = {}
    return res

  # -------------------------------------------------------------------------------
  def fetch_page(self, endpoint):
    if self._client is None:
      self.login()

    if self.verbose:
      print(f'Fetching: {endpoint}')

    pres = self._client.get(endpoint, cookies=self._client.cookies)
    res = pres.text
    return res

  # -------------------------------------------------------------------------------
  def close(self):
    try:
      self._client.close()
    except Exception as e:
      if self.verbose:
        sys.stderr.write('Could not close client properly\n')
        sys.stderr.write(e)

  # -------------------------------------------------------------------------------
  def __del__(self):
    self.close()

  # -------------------------------------------------------------------------------
  @classmethod
  def set_pen(cls, label):
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
  def set_rider_category(cls, div):
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
  def set_category(cls, div):
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
def main():
  """
  Core module for accessing Zwiftpower API endpoints
  """
  zp = ZP()
  zp.verbose = True
  zp.login()
  print(zp.login.status_code)
  zp.close()


# ===============================================================================
if __name__ == '__main__':
  main()
