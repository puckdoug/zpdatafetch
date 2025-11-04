"""Unified Cyclist class with both sync and async fetch capabilities."""

from argparse import ArgumentParser
from typing import Any

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Cyclist(ZP_obj):
  """Fetches and stores cyclist profile data from Zwiftpower.

  Retrieves cyclist information including performance metrics, race history,
  and profile details using Zwift IDs. Supports both synchronous and
  asynchronous operations.

  Synchronous usage:
    cyclist = Cyclist()
    cyclist.fetch(123456, 789012)
    print(cyclist.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      cyclist = Cyclist()
      cyclist.set_session(zp)
      await cyclist.afetch(123456, 789012)
      print(cyclist.json())

  Attributes:
    raw: Dictionary mapping Zwift IDs to their profile data
    verbose: Enable verbose output for debugging
  """

  _url: str = 'https://zwiftpower.com/cache3/profile/'
  _profile: str = 'https://zwiftpower.com/profile.php?z='
  _url_end: str = '_all.json'

  def __init__(self) -> None:
    """Initialize a new Cyclist instance."""
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
  def fetch(self, *zwift_id: int) -> dict[Any, Any]:
    """Fetch cyclist profile data for one or more Zwift IDs (synchronous).

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
    logger.info(f'Fetching cyclist data for {len(zwift_id)} ID(s)')

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
      except (ValueError, TypeError) as e:
        if isinstance(e, ValueError) and 'Invalid Zwift ID' in str(e):
          raise
        raise ValueError(
          f'Invalid Zwift ID: {z}. Must be a valid positive integer.',
        ) from e

    zp = ZP()

    for z in validated_ids:
      logger.debug(f'Fetching cyclist profile for Zwift ID: {z}')
      url = f'{self._url}{z}{self._url_end}'
      x = zp.fetch_json(url)
      self.raw[z] = x
      prof = f'{self._profile}{z}'
      zp.fetch_page(prof)
      logger.debug(f'Successfully fetched data for Zwift ID: {z}')

    logger.info(f'Successfully fetched {len(validated_ids)} cyclist profile(s)')
    return self.raw

  # -------------------------------------------------------------------------------
  async def afetch(self, *zwift_id: int) -> dict[Any, Any]:
    """Fetch cyclist profile data for one or more Zwift IDs (asynchronous).

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
def main() -> None:
  desc = """
Module for fetching cyclist data using the Zwiftpower API
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
    help='raw results',
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
