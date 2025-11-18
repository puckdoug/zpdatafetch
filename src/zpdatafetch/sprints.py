"""Unified Sprints class with both sync and async fetch capabilities."""

from argparse import ArgumentParser
from typing import Any

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Sprints(ZP_obj):
  """Fetches and stores race sprint data from Zwiftpower.

  Retrieves sprint segment results for races using the event_sprints API.
  Supports both synchronous and asynchronous operations.

  Synchronous usage:
    sprints = Sprints()
    sprints.fetch(3590800, 3590801)
    print(sprints.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      sprints = Sprints()
      sprints.set_session(zp)
      await sprints.afetch(3590800, 3590801)
      print(sprints.json())

  Attributes:
    raw: Dictionary mapping race IDs to their sprint data
    verbose: Enable verbose output for debugging
  """

  # https://zwiftpower.com/api3.php?do=event_sprints&zid=<race_id>
  _url: str = 'https://zwiftpower.com/api3.php?do=event_sprints&zid='

  def __init__(self) -> None:
    """Initialize a new Sprints instance."""
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
    """Fetch sprint data for one or more race IDs (synchronous).

    Retrieves sprint segment results for each race ID.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their sprint data

    Raises:
      ValueError: If any race ID is invalid
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    logger.info(f'Fetching sprint data for {len(race_id)} race(s)')

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
      logger.debug(f'Fetching sprint data for race ID: {r}')
      url = f'{self._url}{r}'
      content[r] = zp.fetch_json(url)
      logger.debug(f'Successfully fetched sprints for race ID: {r}')

    self.raw = content
    logger.info(f'Successfully fetched {len(validated_ids)} race sprint(s)')

    return self.raw

  # -------------------------------------------------------------------------------
  async def afetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch sprint data for one or more race IDs (asynchronous).

    Retrieves sprint segment results for each race ID.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their sprint data

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
      logger.info(f'Fetching sprint data for {len(race_id)} race(s) (async)')

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

      # Fetch sprint data for all validated IDs
      for rid in validated_ids:
        url = f'{self._url}{rid}'
        logger.debug(f'Fetching sprint data from: {url}')
        self.raw[rid] = await self._zp.fetch_json(url)
        logger.info(f'Successfully fetched sprints for race ID: {rid}')

      return self.raw

    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zp:
        await self._zp.close()


# ===============================================================================
def main() -> None:
  desc = """
Module for fetching sprints using the Zwiftpower API
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

  x = Sprints()
  if args.verbose:
    x.verbose = True

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
