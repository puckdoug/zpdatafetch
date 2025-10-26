"""Async version of the Cyclist class for fetching cyclist profile data."""

from argparse import ArgumentParser
from typing import Any

import anyio

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class AsyncCyclist(ZP_obj):
  """Async version of Cyclist class for fetching cyclist profile data.

  Retrieves cyclist information including performance metrics, race history,
  and profile details using Zwift IDs asynchronously.

  Usage:
    async with AsyncZP() as zp:
      cyclist = AsyncCyclist()
      cyclist.set_session(zp)
      await cyclist.fetch(123456, 789012)
      print(cyclist.json())

  Attributes:
    raw: Dictionary mapping Zwift IDs to their profile data
  """

  _url: str = 'https://zwiftpower.com/cache3/profile/'
  _profile: str = 'https://zwiftpower.com/profile.php?z='
  _url_end: str = '_all.json'

  def __init__(self) -> None:
    """Initialize a new AsyncCyclist instance."""
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
  async def fetch(self, *zwift_id: int) -> dict[Any, Any]:
    """Fetch cyclist profile data for one or more Zwift IDs (async).

    Retrieves comprehensive profile data from Zwiftpower cache and profile
    pages. Stores results in the raw dictionary keyed by Zwift ID.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to their profile data

    Raises:
      ValueError: If any ID is invalid (non-positive or too large)
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
      logger.info(f'Fetching cyclist data for {len(zwift_id)} ID(s) (async)')

      # SECURITY: Validate all input IDs before processing
      validated_ids = []
      for z in zwift_id:
        try:
          # Convert to int if string, validate range
          zid = int(z) if not isinstance(z, int) else z
          if zid <= 0 or zid > 999999999:
            raise ValueError(
              f'Invalid Zwift ID: {z}. Must be a positive integer.',
            )
          validated_ids.append(zid)
          logger.debug(f'Validated Zwift ID: {zid}')
        except (ValueError, TypeError) as e:
          logger.error(f'Invalid Zwift ID: {z}')
          raise ValueError(f'Invalid Zwift ID: {z}. {e}') from e

      # Fetch data for all validated IDs
      for zid in validated_ids:
        url = f'{self._url}{zid}{self._url_end}'
        logger.debug(f'Fetching cyclist data from: {url}')
        self.raw[zid] = await self._zp.fetch_json(url)
        logger.info(f'Successfully fetched data for Zwift ID: {zid}')

      return self.raw

    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zp:
        await self._zp.close()


# ===============================================================================
async def main() -> None:
  """Example usage of AsyncCyclist class."""
  parser = ArgumentParser(
    description='Fetch cyclist profile data from Zwiftpower (async)',
  )
  parser.add_argument(
    'zwift_ids',
    metavar='ID',
    type=int,
    nargs='+',
    help='One or more Zwift IDs to fetch',
  )
  parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='Enable verbose output',
  )
  args = parser.parse_args()

  async with AsyncZP() as zp:
    cyclist = AsyncCyclist()
    cyclist.set_session(zp)
    await cyclist.fetch(*args.zwift_ids)
    print(cyclist.json())


if __name__ == '__main__':
  anyio.run(main)
