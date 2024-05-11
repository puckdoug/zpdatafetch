# import js2py
from argparse import ArgumentParser
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj


# ===============================================================================
class Cyclist(ZP_obj):
  _url = 'https://zwiftpower.com/cache3/profile/'
  _profile = 'https://zwiftpower.com/profile.php?z='
  _url_end = '_all.json'

  # -------------------------------------------------------------------------------
  # def extract_zp_vars(self, y):
  #   soupjs = BeautifulSoup(y, 'lxml')
  #   f = soupjs.find_all('script')
  #   zp_js = ''
  #   zp_vars = {}
  #   for s in f:
  #     c = s.string
  #     try:
  #       if re.search('ZP_VARS =', c):
  #         zp_js = c
  #     except Exception:
  #       pass

  #   zp_js = zp_js + '; ZP_VARS.athlete_id'
  #   strava = js2py.eval_js(zp_js)
  #   zp_vars['strava'] = f'https://www.strava.com/athletes/{strava}'
  #   return zp_vars

  # -------------------------------------------------------------------------------
  def fetch(self, *zwift_id):
    zp = ZP()
    if self.verbose:
      zp.verbose = True

    for z in zwift_id:
      url = f'{self._url}{z}{self._url_end}'
      x = zp.fetch_json(url)
      self.raw[z] = x
      prof = f'{self._profile}{z}'
      zp.fetch_page(prof)
      # js2py is broken in 3.12 right now. pull request pending to fix it.
      # zp_vars = self.extract_zp_vars(y)

    return self.raw


# ===============================================================================
def main():
  desc = """
Module for fetching cyclist data using the Zwifpower API
  """
  p = ArgumentParser(description=desc)
  p.add_argument(
    '--verbose',
    '-v',
    action='store_const',
    const=True,
    help='provide feedback while running',
  )
  p.add_argument(
    '--raw', '-r', action='store_const', const=True, help='raw results'
  )
  p.add_argument('zwift_id', type=int, nargs='+', help='a list of zwift_ids')
  args = p.parse_args()

  x = Cyclist()

  if args.verbose:
    x.verbose = True

  x.fetch(*args.zwift_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
