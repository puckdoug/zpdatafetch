import datetime
import re
from argparse import ArgumentParser
from typing import Any, Dict, List

from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj


# ===============================================================================
class Primes(ZP_obj):
  """Fetches and stores race prime (sprint/KOM) data from Zwiftpower.

  Retrieves prime segment results for races, including both fastest
  absolute lap (FAL/msec) and first to sprint (FTS/elapsed) primes
  across all categories.

  Attributes:
    raw: Nested dictionary mapping race IDs -> categories -> prime types to data
    verbose: Enable verbose output for debugging
  """

  # https://zwiftpower.com/api3.php?do=event_primes&zid={race_id}&category={cat}&prime_type={type}
  _url_base: str = 'https://zwiftpower.com/api3.php?do=event_primes'
  _url_race_id: str = '&zid='
  _url_category: str = '&category='
  _url_primetype: str = '&prime_type='
  _cat: list[str] = ['A', 'B', 'C', 'D', 'E']
  _type: list[str] = ['msec', 'elapsed']

  def __init__(self) -> None:
    """Initialize a new Primes instance."""
    super().__init__()

  # -------------------------------------------------------------------------------
  @classmethod
  def set_primetype(cls, t: str) -> str:
    """Convert prime type string to Zwiftpower API code.

    Args:
      t: Prime type string ('msec' or 'elapsed')

    Returns:
      API code ('FAL' for fastest absolute lap, 'FTS' for first to sprint,
      or empty string if unknown)
    """
    match t:
      case 'msec':
        return 'FAL'
      case 'elapsed':
        return 'FTS'
      case _:
        return ''

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch prime data for one or more race IDs.

    Retrieves prime results for all categories (A-E) and both prime types
    (msec/FAL and elapsed/FTS) for each race.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Nested dictionary: {race_id: {category: {prime_type: data}}}

    Raises:
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    zp = ZP()
    p: dict[Any, Any] = {}

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
            if 'data' not in res or len(res['data']) == 0:
              print(f'No Results for {primetype} in pen {cat}')
            else:
              print(f'Results found for {primetype} in pen {cat}')
          p[race][cat][primetype] = res
          ts = ts + 1

    self.raw = p

    return self.raw


# ===============================================================================
def main() -> None:
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
