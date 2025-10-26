from argparse import ArgumentParser
from typing import Any

from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Signup(ZP_obj):
  """Fetches and stores race signup data from Zwiftpower.

  Retrieves lists of riders who have signed up for races, including
  their registration details and categories.

  Attributes:
    raw: Dictionary mapping race IDs to their signup data
    verbose: Enable verbose output for debugging
  """

  # race = "https://zwiftpower.com/cache3/results/3590800_signups.json"
  _url: str = 'https://zwiftpower.com/cache3/results/'
  _url_end: str = '_signups.json'

  def __init__(self) -> None:
    """Initialize a new Signup instance."""
    super().__init__()

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id_list: int) -> dict[Any, Any]:
    """Fetch race signup data for one or more race IDs.

    Retrieves the list of signed-up participants from Zwiftpower cache.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id_list: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their signup data

    Raises:
      ValueError: If any race ID is invalid
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    logger.info(f'Fetching race signups for {len(race_id_list)} race(s)')

    # SECURITY: Validate all race IDs before processing
    validated_ids = []
    for r in race_id_list:
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
    signups_by_race_id: dict[Any, Any] = {}

    for race_id in validated_ids:
      logger.debug(f'Fetching race signups for race ID: {race_id}')
      url = f'{self._url}{race_id}{self._url_end}'
      signups_by_race_id[race_id] = zp.fetch_json(url)
      logger.debug(f'Successfully fetched signups for race ID: {race_id}')

    self.raw = signups_by_race_id
    logger.info(f'Successfully fetched {len(race_id_list)} race signup list(s)')

    return self.raw


# ===============================================================================
def main() -> None:
  p = ArgumentParser(
    description='Module for fetching race signup data using the Zwifpower API',
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
  p.add_argument('race_id', type=int, nargs='+', help='one or more race_ids')
  args = p.parse_args()

  x = Signup()
  if args.verbose:
    x.verbose = True

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
