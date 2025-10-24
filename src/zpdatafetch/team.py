import logging
from argparse import ArgumentParser
from typing import Any, Dict

from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Team(ZP_obj):
  """Fetches and stores team roster data from Zwiftpower.

  Retrieves team member lists and associated rider information using
  team IDs.

  Attributes:
    raw: Dictionary mapping team IDs to their roster data
    verbose: Enable verbose output for debugging
  """

  # "https://zwiftpower.com/cache3/teams/{team_id}_riders.json"
  _url: str = 'https://zwiftpower.com/cache3/teams/'
  _url_end: str = '_riders.json'

  def __init__(self) -> None:
    """Initialize a new Team instance."""
    super().__init__()

  # -------------------------------------------------------------------------------
  def fetch(self, *team_id: int) -> dict[Any, Any]:
    """Fetch team roster data for one or more team IDs.

    Retrieves the complete list of team members from Zwiftpower cache.
    Stores results in the raw dictionary keyed by team ID.

    Args:
      *team_id: One or more team ID integers to fetch

    Returns:
      Dictionary mapping team IDs to their roster data

    Raises:
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    logger.info(f'Fetching team data for {len(team_id)} ID(s)')
    zp = ZP()
    content: dict[Any, Any] = {}

    for t in team_id:
      logger.debug(f'Fetching team roster for team ID: {t}')
      url = f'{self._url}{t}{self._url_end}'
      content[t] = zp.fetch_json(url)
      logger.debug(f'Successfully fetched data for team ID: {t}')

    self.raw = content
    logger.info(f'Successfully fetched {len(team_id)} team roster(s)')

    return self.raw


# ===============================================================================
def main() -> None:
  p = ArgumentParser(
    description='Module for fetching cyclist data using the Zwifpower API',
  )
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
  p.add_argument('team_id', type=int, nargs='+', help='a list of team_ids')
  args = p.parse_args()

  x = Team()

  if args.verbose:
    x.verbose = True

  x.fetch(*args.team_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
