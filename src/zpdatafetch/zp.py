import httpx
from zpdatafetch.config import Config
from bs4 import BeautifulSoup
import json


# ===============================================================================
class ZP:
  _client: httpx.Client = None
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
    self._client = httpx.Client(follow_redirects=True)
    page = self._client.get(
      'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
    )
    self._client.cookies.get('phpbb3_lswlk_sid')
    soup = BeautifulSoup(page.text, 'lxml')
    login_url = soup.form['action'][0:]
    data = {'username': self.username, 'password': self.password}
    self.login = self._client.post(
      login_url, data=data, cookies=self._client.cookies
    )

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
    except Exception:
      pass

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
