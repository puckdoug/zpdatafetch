"""Async version of the ZRTeam class for fetching team roster data."""

from argparse import ArgumentParser

import anyio

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.exceptions import ZRConfigError, ZRNetworkError
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zrteam import ZRTeam

logger = get_logger(__name__)


# ===============================================================================
class AsyncZRTeam(ZRTeam):
  """Async version of ZRTeam class for fetching team roster data.

  Retrieves team roster information including all team members and their
  rating and power metrics asynchronously.

  Usage:
    async with AsyncZR_obj() as zr:
      team = AsyncZRTeam()
      team.set_session(zr)
      await team.fetch(team_id=456)
      print(team.json())

  Attributes:
    team_id: The team/club ID
    team_name: Name of the team/club
    riders: List of ZRTeamRider objects for team members
  """

  def __init__(self) -> None:
    """Initialize a new AsyncZRTeam instance."""
    super().__init__()
    self._zr: AsyncZR_obj | None = None

  # -------------------------------------------------------------------------------
  def set_session(self, zr: AsyncZR_obj) -> None:
    """Set the AsyncZR_obj session to use for fetching data.

    Args:
      zr: AsyncZR_obj instance to use for API requests
    """
    self._zr = zr

  # -------------------------------------------------------------------------------
  async def fetch(self, team_id: int | None = None) -> None:
    """Fetch team roster data from the Zwiftracing API (async).

    Fetches all team members and their data for a specific team ID from
    the Zwiftracing API.

    Args:
      team_id: The team ID to fetch (uses self.team_id if not provided)

    Raises:
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      team = AsyncZRTeam()
      team.set_session(zr)
      await team.fetch(team_id=456)
      print(team.json())
    """
    # Use provided value or default
    if team_id is not None:
      self.team_id = team_id

    if self.team_id == 0:
      logger.warning('No team_id provided for fetch')
      return

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(f'Fetching team roster for team_id={self.team_id} (async)')

    # Create temporary session if none provided
    if not self._zr:
      self._zr = AsyncZR_obj()
      await self._zr.init_client()
      owns_session = True
    else:
      owns_session = False

    try:
      # Endpoint is /public/clubs/{team_id}/0 (0 is starting rider offset)
      endpoint = f'/public/clubs/{self.team_id}/0'

      # Fetch JSON from API
      headers = {'Authorization': config.authorization}
      self._raw = await self._zr.fetch_json(endpoint, headers=headers)

      # Parse response
      self._parse_response()
      logger.info(f'Successfully fetched team roster for team_id={self.team_id}')
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch team roster: {e}')
      raise
    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zr:
        await self._zr.close()


# ===============================================================================
async def main() -> None:
  """Example usage of AsyncZRTeam class."""
  parser = ArgumentParser(
    description='Fetch team rosters from Zwiftracing (async)',
  )
  parser.add_argument(
    'team_ids',
    metavar='ID',
    type=int,
    nargs='+',
    help='One or more team IDs to fetch',
  )
  args = parser.parse_args()

  async with AsyncZR_obj() as zr:
    for team_id in args.team_ids:
      team = AsyncZRTeam()
      team.set_session(zr)
      await team.fetch(team_id=team_id)
      print(team.json())


if __name__ == '__main__':
  anyio.run(main)
