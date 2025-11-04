"""Unified Result class with both sync and async fetch capabilities."""

from argparse import ArgumentParser
from typing import Any

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Result(ZP_obj):
  """Fetches and stores race results from Zwiftpower.

  Retrieves complete race result data including participant placements,
  times, and performance metrics using race IDs. Supports both synchronous
  and asynchronous operations.

  Synchronous usage:
    result = Result()
    result.fetch(3590800, 3590801)
    print(result.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      result = Result()
      result.set_session(zp)
      await result.afetch(3590800, 3590801)
      print(result.json())

  Attributes:
    raw: Dictionary mapping race IDs to their result data
    verbose: Enable verbose output for debugging
  """

  # race = "https://zwiftpower.com/cache3/results/3590800_view.json"
  _url: str = 'https://zwiftpower.com/cache3/results/'
  _url_end: str = '_view.json'

  def __init__(self) -> None:
    """Initialize a new Result instance."""
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
  def fetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch race results for one or more race IDs (synchronous).

    Retrieves comprehensive race result data from Zwiftpower cache.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their result data

    Raises:
      ValueError: If any race ID is invalid
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    logger.info(f'Fetching race results for {len(race_id)} race(s)')

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
    content: dict[Any, Any] = {}

    for r in validated_ids:
      logger.debug(f'Fetching race results for race ID: {r}')
      url = f'{self._url}{r}{self._url_end}'
      content[r] = zp.fetch_json(url)
      logger.debug(f'Successfully fetched results for race ID: {r}')

    self.raw = content
    logger.info(f'Successfully fetched {len(validated_ids)} race result(s)')

    return self.raw

  # -------------------------------------------------------------------------------
  async def afetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch race results for one or more race IDs (asynchronous).

    Retrieves comprehensive race result data from Zwiftpower cache.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their result data

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
      logger.info(f'Fetching race results for {len(race_id)} race(s) (async)')

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

      # Fetch results for all validated IDs
      for rid in validated_ids:
        url = f'{self._url}{rid}{self._url_end}'
        logger.debug(f'Fetching race results from: {url}')
        self.raw[rid] = await self._zp.fetch_json(url)
        logger.info(f'Successfully fetched results for race ID: {rid}')

      return self.raw

    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zp:
        await self._zp.close()


# ===============================================================================
def main() -> None:
  desc = """
Module for fetching race data using the Zwiftpower API
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
