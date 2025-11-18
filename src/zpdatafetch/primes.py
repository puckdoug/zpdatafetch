"""Unified Primes class with both sync and async fetch capabilities."""

import datetime
import re
from argparse import ArgumentParser
from typing import Any

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Primes(ZP_obj):
  """Fetches and stores race prime (sprint/KOM) data from Zwiftpower.

  Retrieves prime segment results for races, including both fastest
  absolute lap (FAL/msec) and first to sprint (FTS/elapsed) primes
  across all categories. Supports both synchronous and asynchronous operations.

  Synchronous usage:
    primes = Primes()
    primes.fetch(3590800, 3590801)
    print(primes.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      primes = Primes()
      primes.set_session(zp)
      await primes.afetch(3590800, 3590801)
      print(primes.json())

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

  # Async version uses different URLs
  _url_async: str = 'https://zwiftpower.com/cache3/primes/'
  _url_end_async: str = '.json'

  def __init__(self) -> None:
    """Initialize a new Primes instance."""
    super().__init__()
    self._zp: AsyncZP | None = None

  # -------------------------------------------------------------------------------
  def set_session(self, zp: AsyncZP) -> None:
    """Set the AsyncZP session to use for async fetching.

    Args:
      zp: AsyncZP instance to use for API requests
    """
    self._zp = zp

  # -------------------------------------------------------------------------------
  @classmethod
  def set_primetype(cls, t: str) -> str:
    """Convert prime type string to Zwiftpower API code or descriptive string.

    Args:
      t: Prime type string ('msec', 'elapsed', 'sprint', 'kom', 'prime')

    Returns:
      API code ('FAL' for fastest absolute lap, 'FTS' for first to sprint,
      or descriptive string like 'Sprint', 'KOM', 'Prime', or empty string for unknown)
    """
    match t.lower():
      case 'msec':
        return 'FAL'
      case 'elapsed':
        return 'FTS'
      case 'sprint':
        return 'Sprint'
      case 'kom':
        return 'KOM'
      case 'prime':
        return 'Prime'
      case _:
        return ''

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch prime data for one or more race IDs (synchronous).

    Retrieves prime results for all categories (A-E) and both prime types
    (msec/FAL and elapsed/FTS) for each race.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Nested dictionary: {race_id: {category: {prime_type: data}}}

    Raises:
      ValueError: If any race ID is invalid
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    logger.info(f'Fetching prime data for {len(race_id)} race(s)')

    # SECURITY: Validate all race IDs before processing
    validated_ids = []
    for r in race_id:
      try:
        # Convert to int if string, validate range
        rid = int(r) if not isinstance(r, int) else r
        if rid <= 0 or rid > 999999999:
          raise ValueError(
            f'Invalid race ID: {r}. Must be a positive integer.',
          )
        validated_ids.append(rid)
      except (ValueError, TypeError) as e:
        if isinstance(e, ValueError) and 'Invalid race ID' in str(e):
          raise
        raise ValueError(
          f'Invalid race ID: {r}. Must be a valid positive integer.',
        ) from e

    zp = ZP()
    p: dict[Any, Any] = {}

    ts = int(re.sub(r'\.', '', str(datetime.datetime.now().timestamp())[:-3]))

    for race in validated_ids:
      logger.debug(f'Fetching primes for race ID: {race}')
      p[race] = {}
      for cat in self._cat:
        if cat not in p[race]:
          p[race][cat] = {}
        for primetype in self._type:
          logger.debug(f'Fetching {primetype} primes for category {cat}')
          url = f'{self._url_base}{self._url_race_id}{race}{self._url_category}{cat}{self._url_primetype}{primetype}&_={ts}'
          res = zp.fetch_json(url)
          if 'data' not in res or len(res['data']) == 0:
            logger.debug(f'No results for {primetype} in category {cat}')
          else:
            logger.debug(f'Results found for {primetype} in category {cat}')
          p[race][cat][primetype] = res
          ts = ts + 1
      logger.debug(f'Successfully fetched all primes for race ID: {race}')

    self.raw = p
    logger.info(f'Successfully fetched prime data for {len(validated_ids)} race(s)')

    return self.raw

  # -------------------------------------------------------------------------------
  async def afetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch prime data for one or more race IDs (asynchronous).

    Retrieves prime results for all categories (A-E) and both prime types
    (msec/FAL and elapsed/FTS) for each race.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Nested dictionary: {race_id: {category: {prime_type: data}}}

    Raises:
      ValueError: If any race ID is invalid
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    if not self._zp:
      # Create a temporary session if none provided
      self._zp = AsyncZP()
      await self._zp.login()
      owns_session = True
    else:
      owns_session = False

    try:
      logger.info(f'Fetching prime data for {len(race_id)} race(s) (async)')

      # SECURITY: Validate all race IDs before processing
      validated_ids = []
      for r in race_id:
        try:
          # Convert to int if string, validate range
          rid = int(r) if not isinstance(r, int) else r
          if rid <= 0 or rid > 999999999:
            raise ValueError(
              f'Invalid race ID: {r}. Must be a positive integer.',
            )
          validated_ids.append(rid)
          logger.debug(f'Validated race ID: {rid}')
        except (ValueError, TypeError) as e:
          logger.error(f'Invalid race ID: {r}')
          raise ValueError(f'Invalid race ID: {r}. {e}') from e

      p: dict[Any, Any] = {}
      ts = int(re.sub(r'\.', '', str(datetime.datetime.now().timestamp())[:-3]))

      for race in validated_ids:
        logger.debug(f'Fetching primes for race ID: {race} (async)')
        p[race] = {}
        for cat in self._cat:
          if cat not in p[race]:
            p[race][cat] = {}
          for primetype in self._type:
            logger.debug(f'Fetching {primetype} primes for category {cat} (async)')
            url = f'{self._url_base}{self._url_race_id}{race}{self._url_category}{cat}{self._url_primetype}{primetype}&_={ts}'
            res = await self._zp.fetch_json(url)
            if 'data' not in res or len(res['data']) == 0:
              logger.debug(f'No results for {primetype} in category {cat} (async)')
            else:
              logger.debug(f'Results found for {primetype} in category {cat} (async)')
            p[race][cat][primetype] = res
            ts = ts + 1
        logger.debug(f'Successfully fetched all primes for race ID: {race} (async)')

      self.raw = p
      logger.info(
        f'Successfully fetched prime data for {len(validated_ids)} race(s) (async)'
      )

      return self.raw

    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zp:
        await self._zp.close()


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
