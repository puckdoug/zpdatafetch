"""Async version of the Result class for fetching race results."""

from argparse import ArgumentParser
from typing import Any

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class AsyncResult(ZP_obj):
  """Async version of Result class for fetching race results.

  Retrieves complete race result data including participant placements,
  times, and performance metrics using race IDs asynchronously.

  Usage:
    async with AsyncZP() as zp:
      result = AsyncResult()
      result.set_session(zp)
      await result.fetch(3590800, 3590801)
      print(result.json())

  Attributes:
    raw: Dictionary mapping race IDs to their result data
  """

  _url: str = 'https://zwiftpower.com/cache3/results/'
  _url_end: str = '_view.json'

  def __init__(self) -> None:
    """Initialize a new AsyncResult instance."""
    super().__init__()
    self._zp: AsyncZP | None = None

  # -------------------------------------------------------------------------------
  def set_session(self, zp: AsyncZP) -> None:
    """Set the AsyncZP session to use for fetching data.

    Args:
      zp: AsyncZP instance to use for API requests
    """
    self._zp = zp

  # -------------------------------------------------------------------------------
  async def fetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch race results for one or more race IDs (async).

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
async def main() -> None:
  """Example usage of AsyncResult class."""
  parser = ArgumentParser(
    description='Fetch race results from Zwiftpower (async)',
  )
  parser.add_argument(
    'race_ids',
    metavar='ID',
    type=int,
    nargs='+',
    help='One or more race IDs to fetch',
  )
  parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='Enable verbose output',
  )
  args = parser.parse_args()

  async with AsyncZP() as zp:
    result = AsyncResult()
    result.set_session(zp)
    await result.fetch(*args.race_ids)
    print(result.json())


if __name__ == '__main__':
  import asyncio

  asyncio.run(main())
