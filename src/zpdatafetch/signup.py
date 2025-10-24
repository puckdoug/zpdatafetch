from argparse import ArgumentParser
from typing import Any, Dict

from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj


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
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    zp = ZP()
    signups_by_race_id: dict[Any, Any] = {}
    if self.verbose:
      zp.verbose = True

    for race_id in race_id_list:
      url = f'{self._url}{race_id}{self._url_end}'
      if zp.verbose:
        print(f'fetching: {url}')
      signups_by_race_id[race_id] = zp.fetch_json(url)

    self.raw = signups_by_race_id

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
