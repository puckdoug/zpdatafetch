from argparse import ArgumentParser
from typing import Any, Dict

from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj


# ===============================================================================
class Result(ZP_obj):
  """Fetches and stores race results from Zwiftpower.

  Retrieves complete race result data including participant placements,
  times, and performance metrics using race IDs.

  Attributes:
    raw: Dictionary mapping race IDs to their result data
    verbose: Enable verbose output for debugging
  """

  # race = "https://zwiftpower.com/cache3/results/3590800_view.json"
  _url: str = 'https://zwiftpower.com/cache3/results/'
  _url_end: str = '_view.json'

  def __init__(self) -> None:
    """Initialize a new Result instance."""
    super().__init__()

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch race results for one or more race IDs.

    Retrieves comprehensive race result data from Zwiftpower cache.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their result data

    Raises:
      ZPNetworkError: If network requests fail
      ZPAuthenticationError: If authentication fails
    """
    zp = ZP()
    content: dict[Any, Any] = {}
    if self.verbose:
      zp.verbose = True

    for r in race_id:
      url = f'{self._url}{r}{self._url_end}'
      if zp.verbose:
        print(f'fetching: {url}')
      content[r] = zp.fetch_json(url)

    self.raw = content

    return self.raw


# ===============================================================================
def main() -> None:
  desc = """
Module for fetching race data using the Zwifpower API
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

  x = Result()
  if args.verbose:
    x.verbose = True

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
