"""Async version of the ZRRider class for fetching rider rating data."""

from argparse import ArgumentParser

import anyio

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.exceptions import ZRConfigError, ZRNetworkError
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zrrider import ZRRider

logger = get_logger(__name__)


# ===============================================================================
class AsyncZRRider(ZRRider):
  """Async version of ZRRider class for fetching rider rating data.

  Retrieves rider rating information including current, max30, and max90
  ratings using Zwift IDs asynchronously. Supports both individual and
  batch (POST) requests.

  Usage:
    async with AsyncZR_obj() as zr:
      rider = AsyncZRRider()
      rider.set_session(zr)
      await rider.fetch(123456)
      print(rider.json())

    # Batch fetch
    async with AsyncZR_obj() as zr:
      riders = await AsyncZRRider.fetch_batch(123456, 789012, zr=zr)
      for zwift_id, rider in riders.items():
        print(f"{rider.name}: {rider.current_rating}")

  Attributes:
    raw: Dictionary mapping Zwift IDs to their profile data
  """

  def __init__(self) -> None:
    """Initialize a new AsyncZRRider instance."""
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
  async def fetch(
    self,
    zwift_id: int | None = None,
    epoch: int | None = None,
  ) -> None:
    """Fetch rider rating data from the Zwiftracing API (async).

    Fetches the rider's current or historical rating data based on the
    provided zwift_id and optional epoch (unix timestamp).

    Args:
      zwift_id: Rider's Zwift ID (uses self.zwift_id if not provided)
      epoch: Unix timestamp for historical data (uses self.epoch if not provided)

    Raises:
      ValueError: If zwift_id is invalid
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      rider = AsyncZRRider()
      rider.set_session(zr)
      await rider.fetch(zwift_id=12345)
      print(rider.json())
    """
    # Use provided values or defaults
    if zwift_id is not None:
      self.zwift_id = zwift_id
    if epoch is not None:
      self.epoch = epoch

    if self.zwift_id == 0:
      logger.warning('No zwift_id provided for fetch')
      return

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(
      f'Fetching rider for zwift_id={self.zwift_id}, epoch={self.epoch} (async)',
    )

    # Build endpoint
    if self.epoch >= 0:
      endpoint = f'/public/riders/{self.zwift_id}/{self.epoch}'
    else:
      endpoint = f'/public/riders/{self.zwift_id}'

    # Create temporary session if none provided
    if not self._zr:
      self._zr = AsyncZR_obj()
      await self._zr.init_client()
      owns_session = True
    else:
      owns_session = False

    try:
      # Fetch JSON from API
      headers = {'Authorization': config.authorization}
      self._raw = await self._zr.fetch_json(endpoint, headers=headers)

      # Parse response
      self._parse_response()
      logger.info(
        f'Successfully fetched rider {self.name} (zwift_id={self.zwift_id})',
      )
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch rider: {e}')
      raise
    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zr:
        await self._zr.close()

  # -------------------------------------------------------------------------------
  @staticmethod
  async def fetch_batch(
    *zwift_ids: int,
    epoch: int | None = None,
    zr: AsyncZR_obj | None = None,
  ) -> dict[int, 'ZRRider']:
    """Fetch multiple riders in a single request (POST, async).

    Uses the Zwiftracing API batch endpoint to fetch current or historical
    data for multiple riders in a single request. More efficient than
    individual GET requests.

    Args:
      *zwift_ids: Rider IDs to fetch (max 1000 per request)
      epoch: Unix timestamp for historical data (None for current)
      zr: Optional AsyncZR_obj session. If not provided, creates temporary session.

    Returns:
      Dictionary mapping rider ID to ZRRider instance with parsed data

    Raises:
      ValueError: If more than 1000 IDs provided
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      # With session
      async with AsyncZR_obj() as zr:
        riders = await AsyncZRRider.fetch_batch(12345, 67890, 11111, zr=zr)
        for zwift_id, rider in riders.items():
          print(f"{rider.name}: {rider.current_rating}")

      # Without session (creates temporary)
      riders = await AsyncZRRider.fetch_batch(12345, 67890)

      # Historical data
      riders = await AsyncZRRider.fetch_batch(12345, 67890, epoch=1704067200, zr=zr)
    """
    if len(zwift_ids) > 1000:
      raise ValueError('Maximum 1000 rider IDs per batch request')

    if len(zwift_ids) == 0:
      logger.warning('No rider IDs provided for batch fetch')
      return {}

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(
      f'Fetching batch of {len(zwift_ids)} riders, epoch={epoch} (async)',
    )

    # Create temporary session if none provided
    if not zr:
      zr = AsyncZR_obj()
      await zr.init_client()
      owns_session = True
    else:
      owns_session = False

    try:
      # Build endpoint
      if epoch is not None:
        endpoint = f'/public/riders/{epoch}'
      else:
        endpoint = '/public/riders'

      # Fetch JSON from API using POST
      headers = {'Authorization': config.authorization}
      raw_data = await zr.fetch_json(
        endpoint,
        method='POST',
        headers=headers,
        json=list(zwift_ids),
      )

      # Parse response into individual ZRRider objects
      results = {}
      if not isinstance(raw_data, list):
        logger.error('Expected list of riders in batch response')
        return results

      for rider_data in raw_data:
        try:
          rider = ZRRider()
          rider._raw = rider_data
          rider._parse_response()
          results[rider.zwift_id] = rider
          logger.debug(
            f'Parsed batch rider: {rider.name} (zwift_id={rider.zwift_id})',
          )
        except (KeyError, TypeError) as e:
          logger.warning(f'Skipping malformed rider in batch response: {e}')
          continue

      logger.info(
        f'Successfully fetched {len(results)}/{len(zwift_ids)} riders in batch (async)',
      )
      return results

    except ZRNetworkError as e:
      logger.error(f'Failed to fetch batch: {e}')
      raise
    finally:
      # Clean up temporary session if we created one
      if owns_session and zr:
        await zr.close()


# ===============================================================================
async def main() -> None:
  """Example usage of AsyncZRRider class."""
  parser = ArgumentParser(
    description='Fetch rider rating data from Zwiftracing (async)',
  )
  parser.add_argument(
    'zwift_ids',
    metavar='ID',
    type=int,
    nargs='+',
    help='One or more Zwift IDs to fetch',
  )
  parser.add_argument(
    '-b',
    '--batch',
    action='store_true',
    help='Use batch POST endpoint for multiple IDs',
  )
  parser.add_argument(
    '-e',
    '--epoch',
    type=int,
    help='Unix timestamp for historical data',
  )
  args = parser.parse_args()

  async with AsyncZR_obj() as zr:
    if args.batch:
      riders = await AsyncZRRider.fetch_batch(
        *args.zwift_ids,
        epoch=args.epoch,
        zr=zr,
      )
      for zwift_id, rider in riders.items():
        print(rider.json())
    else:
      for zwift_id in args.zwift_ids:
        rider = AsyncZRRider()
        rider.set_session(zr)
        await rider.fetch(zwift_id=zwift_id, epoch=args.epoch)
        print(rider.json())


if __name__ == '__main__':
  anyio.run(main)
