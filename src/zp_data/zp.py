import httpx
from zp_data.setup import Config
from bs4 import BeautifulSoup


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
    foo = self._client.get(
      'https://zwiftpower.com/ucp.php?mode=login&login=external&oauth_service=oauthzpsso'
    )
    sid = self._client.cookies.get('phpbb3_lswlk_sid')
    soup = BeautifulSoup(foo.text, 'lxml')
    login_url = soup.form['action'][0:]
    data = {'username': self.username, 'password': self.password}
    self.login = self._client.post(
      login_url, data=data, cookies=self._client.cookies
    )

  # -------------------------------------------------------------------------------
  def close(self):
    try:
      self._client.close()
    except Exception:
      pass

  # -------------------------------------------------------------------------------
  def __del__(self):
    self.close()


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
