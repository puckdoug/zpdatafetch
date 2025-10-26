"""Async version of the Team class for fetching team data."""

from argparse import ArgumentParser
from typing import Any

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class AsyncTeam(ZP_obj):
  """Async version of Team class for fetching team information.

  Retrieves team data including member lists and team details asynchronously.

  Usage:
    async with AsyncZP() as zp:
      team = AsyncTeam()
      team.set_session(zp)
      await team.fetch(123, 456)
      print(team.json())

  Attributes:
    raw: Dictionary mapping team IDs to their data
  """

  _url: str = 'https://zwiftpower.com/cache3/teams/'
  _url_end: str = '.json'

  def __init__(self) -> None:
    """Initialize a new AsyncTeam instance."""
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
  async def fetch(self, *team_id: int) -> dict[Any, Any]:
    """Fetch team data for one or more team IDs (async).

    Retrieves team information from Zwiftpower cache.
    Stores results in the raw dictionary keyed by team ID.

    Args:
      *team_id: One or more team ID integers to fetch

    Returns:
      Dictionary mapping team IDs to their data

    Raises:
      ValueError: If any team ID is invalid
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
      logger.info(f'Fetching team data for {len(team_id)} team(s) (async)')

      # SECURITY: Validate all team IDs before processing
      validated_ids = []
      for t in team_id:
        try:
          # Convert to int if string, validate range
          tid = int(t) if not isinstance(t, int) else t
          if tid <= 0 or tid > 999999999:
            raise ValueError(
              f'Invalid team ID: {t}. Must be a positive integer.',
            )
          validated_ids.append(tid)
          logger.debug(f'Validated team ID: {tid}')
        except (ValueError, TypeError) as e:
          logger.error(f'Invalid team ID: {t}')
          raise ValueError(f'Invalid team ID: {t}. {e}') from e

      # Fetch data for all validated team IDs
      for tid in validated_ids:
        url = f'{self._url}{tid}{self._url_end}'
        logger.debug(f'Fetching team data from: {url}')
        self.raw[tid] = await self._zp.fetch_json(url)
        logger.info(f'Successfully fetched data for team ID: {tid}')

      return self.raw

    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zp:
        await self._zp.close()


# ===============================================================================
async def main() -> None:
  """Example usage of AsyncTeam class."""
  parser = ArgumentParser(
    description='Fetch team data from Zwiftpower (async)',
  )
  parser.add_argument(
    'team_ids',
    metavar='ID',
    type=int,
    nargs='+',
    help='One or more team IDs to fetch',
  )
  parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='Enable verbose output',
  )
  args = parser.parse_args()

  async with AsyncZP() as zp:
    team = AsyncTeam()
    team.set_session(zp)
    await team.fetch(*args.team_ids)
    print(team.json())


if __name__ == '__main__':
  import asyncio

  asyncio.run(main())
