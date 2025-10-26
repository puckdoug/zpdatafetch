# import js2py
from argparse import ArgumentParser
from typing import Any

from zpdatafetch.logging_config import get_logger
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Cyclist(ZP_obj):
  """Fetches and stores cyclist profile data from Zwiftpower.

  Retrieves cyclist information including performance metrics, race history,
  and profile details using Zwift IDs.

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

  # -------------------------------------------------------------------------------
  # def extract_zp_vars(self, y):
  #   soupjs = BeautifulSoup(y, 'lxml')
  #   f = soupjs.find_all('script')
  #   zp_js = ''
  #   zp_vars = {}
  #   for s in f:
  #     c = s.string
  #     try:
  #       if re.search('ZP_VARS =', c):
  #         zp_js = c
  #     except Exception:
  #       pass

  #   zp_js = zp_js + '; ZP_VARS.athlete_id'
  #   strava = js2py.eval_js(zp_js)
  #   zp_vars['strava'] = f'https://www.strava.com/athletes/{strava}'
  #   return zp_vars

  # -------------------------------------------------------------------------------
  def fetch(self, *zwift_id: int) -> dict[Any, Any]:
    """Fetch cyclist profile data for one or more Zwift IDs.

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
    for z in zwift_id:
      if not isinstance(z, int) or z <= 0 or z > 999999999:
        raise ValueError(
          f'Invalid Zwift ID: {z}. Must be a positive integer.',
        )

    zp = ZP()

    for z in zwift_id:
      logger.debug(f'Fetching cyclist profile for Zwift ID: {z}')
      url = f'{self._url}{z}{self._url_end}'
      x = zp.fetch_json(url)
      self.raw[z] = x
      prof = f'{self._profile}{z}'
      zp.fetch_page(prof)
      logger.debug(f'Successfully fetched data for Zwift ID: {z}')
      # js2py is broken in 3.12 right now. pull request pending to fix it.
      # zp_vars = self.extract_zp_vars(y)

    logger.info(f'Successfully fetched {len(zwift_id)} cyclist profile(s)')
    return self.raw


# ===============================================================================
def main() -> None:
  desc = """
Module for fetching cyclist data using the Zwifpower API
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
