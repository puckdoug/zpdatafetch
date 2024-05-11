from argparse import ArgumentParser
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj


# ===============================================================================
class Signup(ZP_obj):
  # race = "https://zwiftpower.com/cache3/results/3590800_signups.json"
  _url = 'https://zwiftpower.com/cache3/results/'
  _url_end = '_signups.json'

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id_list):
    zp = ZP()
    signups_by_race_id = {}
    if self.verbose:
      zp.verbose = True

    for race_id in race_id_list:
      url = f'{self._url}{race_id}{self._url_end}'
      if zp.verbose:
        print(f'fetching: {url}')
      signups_by_race_id[race_id] = zp.fetch_json(url)

    self.raw = signups_by_race_id

    return self.raw


# ===============================================================================
def main():
  p = ArgumentParser(
    description='Module for fetching race signup data using the Zwifpower API'
  )
  p.add_argument(
    '--verbose',
    '-v',
    action='store_const',
    const=True,
    help='provide feedback while running',
  )
  p.add_argument(
    '--raw',
    '-r',
    action='store_const',
    const=True,
    help='print all returned data',
  )
  p.add_argument('race_id', type=int, nargs='+', help='one or more race_ids')
  args = p.parse_args()

  x = Signup()
  if args.verbose:
    x.verbose = True

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
