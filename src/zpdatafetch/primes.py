import re
import datetime
from argparse import ArgumentParser
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj


# ===============================================================================
class Primes(ZP_obj):
  # https://zwiftpower.com/api3.php?do=event_primes&zid={race_id}&category={cat}&prime_type={type}
  _url_base = 'https://zwiftpower.com/api3.php?do=event_primes'
  _url_race_id = '&zid='
  _url_category = '&category='
  _url_primetype = '&prime_type='
  _cat = ['A', 'B', 'C', 'D', 'E']
  _type = ['msec', 'elapsed']

  # -------------------------------------------------------------------------------
  @classmethod
  def set_primetype(cls, t):
    match t:
      case 'msec':
        return 'FAL'
      case 'elapsed':
        return 'FTS'
      case _:
        return ''

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id):
    zp = ZP()
    p = {}

    ts = int(re.sub(r'\.', '', str(datetime.datetime.now().timestamp())[:-3]))

    if self.verbose:
      zp.verbose = True

    for race in race_id:
      p[race] = {}
      for cat in self._cat:
        if cat not in p[race]:
          p[race][cat] = {}
        for primetype in self._type:
          url = f'{self._url_base}{self._url_race_id}{race}{self._url_category}{cat}{self._url_primetype}{primetype}&_={ts}'
          res = zp.fetch_json(url)
          if self.verbose:
            if 'data' not in res:
              print(f'No Results for {primetype} in pen {cat}')
            elif len(res['data']) == 0:
              print(f'No Results for {primetype} in pen {cat}')
            else:
              print(f'Results found for {primetype} in pen {cat}')
          p[race][cat][primetype] = res
          ts = ts + 1

    self.raw = p

    return self.raw


# ===============================================================================
def main():
  desc = """
Module for fetching primes using the Zwiftpower API
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

  x = Primes()
  if args.verbose:
    x.verbose = True

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
