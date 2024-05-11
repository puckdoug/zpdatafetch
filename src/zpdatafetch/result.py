from argparse import ArgumentParser
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj


# ===============================================================================
class Result(ZP_obj):
  # race = "https://zwiftpower.com/cache3/results/3590800_view.json"
  _url = 'https://zwiftpower.com/cache3/results/'
  _url_end = '_view.json'
  raw = None
  verbose = False

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id):
    zp = ZP()
    content = {}
    if self.verbose:
      zp.verbose = True

    for r in race_id:
      url = f'{self._url}{r}{self._url_end}'
      if zp.verbose:
        print(f'fetching: {url}')
      content[r] = zp.fetch_json(url)

    self.raw = content

    return self.raw


# ===============================================================================
def main():
  desc = """
Module for fetching race data using the Zwifpower API
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
    '--raw',
    '-r',
    action='store_const',
    const=True,
    help='print all returned data',
  )
  p.add_argument('race_id', type=int, nargs='+', help='one or more race_ids')
  args = p.parse_args()

  x = Result()
  if args.verbose:
    x.verbose = True

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
