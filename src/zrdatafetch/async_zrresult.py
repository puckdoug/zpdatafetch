"""Async version of the ZRResult class for fetching race result data."""

from argparse import ArgumentParser

import anyio

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.exceptions import ZRConfigError, ZRNetworkError
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zrresult import ZRResult

logger = get_logger(__name__)


# ===============================================================================
class AsyncZRResult(ZRResult):
  """Async version of ZRResult class for fetching race result data.

  Retrieves race result information including all rider finishes and rating
  changes asynchronously.

  Usage:
    async with AsyncZR_obj() as zr:
      result = AsyncZRResult()
      result.set_session(zr)
      await result.fetch(race_id=3590800)
      print(result.json())

  Attributes:
    race_id: The race ID
    results: List of ZRRiderResult objects for each participant
  """

  def __init__(self) -> None:
    """Initialize a new AsyncZRResult instance."""
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
  async def fetch(self, race_id: int | None = None) -> None:
    """Fetch race result data from the Zwiftracing API (async).

    Fetches all rider results for a specific race ID from the Zwiftracing API.

    Args:
      race_id: The race ID to fetch (uses self.race_id if not provided)

    Raises:
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      result = AsyncZRResult()
      result.set_session(zr)
      await result.fetch(race_id=3590800)
      print(result.json())
    """
    # Use provided value or default
    if race_id is not None:
      self.race_id = race_id

    if self.race_id == 0:
      logger.warning('No race_id provided for fetch')
      return

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(f'Fetching results for race_id={self.race_id} (async)')

    # Create temporary session if none provided
    if not self._zr:
      self._zr = AsyncZR_obj()
      await self._zr.init_client()
      owns_session = True
    else:
      owns_session = False

    try:
      # Endpoint is /public/results/{race_id}
      endpoint = f'/public/results/{self.race_id}'

      # Fetch JSON from API
      headers = {'Authorization': config.authorization}
      self._raw = await self._zr.fetch_json(endpoint, headers=headers)

      # Parse response
      self._parse_response()
      logger.info(f'Successfully fetched results for race_id={self.race_id}')
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch race result: {e}')
      raise
    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zr:
        await self._zr.close()


# ===============================================================================
async def main() -> None:
  """Example usage of AsyncZRResult class."""
  parser = ArgumentParser(
    description='Fetch race results from Zwiftracing (async)',
  )
  parser.add_argument(
    'race_ids',
    metavar='ID',
    type=int,
    nargs='+',
    help='One or more race IDs to fetch',
  )
  args = parser.parse_args()

  async with AsyncZR_obj() as zr:
    for race_id in args.race_ids:
      result = AsyncZRResult()
      result.set_session(zr)
      await result.fetch(race_id=race_id)
      print(result.json())


if __name__ == '__main__':
  anyio.run(main)
