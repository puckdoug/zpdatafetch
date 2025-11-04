"""Unified ZRRider class with both sync and async fetch capabilities.

This module provides the ZRRider class for fetching and storing rider
rating data from the Zwiftracing API.
"""

from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.exceptions import ZRConfigError, ZRNetworkError
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr import ZR_obj

logger = get_logger(__name__)


# ===============================================================================
@dataclass
class ZRRider(ZR_obj):
  """Rider rating data from Zwiftracing API.

  Represents a rider's current and historical ratings across multiple
  timeframes (current, max30, max90) as well as derived rating score (DRS).
  Supports both synchronous and asynchronous operations.

  Synchronous usage:
    rider = ZRRider()
    rider.fetch(zwift_id=12345)
    print(rider.json())

    # Batch fetch
    riders = ZRRider.fetch_batch(123456, 789012)
    for zwift_id, rider in riders.items():
      print(f"{rider.name}: {rider.current_rating}")

  Asynchronous usage:
    async with AsyncZR_obj() as zr:
      rider = ZRRider()
      rider.set_session(zr)
      await rider.afetch(zwift_id=123456)
      print(rider.json())

    # Async batch fetch
    async with AsyncZR_obj() as zr:
      riders = await ZRRider.afetch_batch(123456, 789012, zr=zr)
      for zwift_id, rider in riders.items():
        print(f"{rider.name}: {rider.current_rating}")

  Attributes:
    zwift_id: Rider's Zwift ID
    epoch: Unix timestamp for historical data (default: -1 for current)
    name: Rider's display name
    gender: Rider's gender (M/F)
    current_rating: Current rating score
    current_rank: Current category rank
    max30_rating: Maximum rating in last 30 days
    max30_rank: Max30 category rank
    max90_rating: Maximum rating in last 90 days
    max90_rank: Max90 category rank
    drs_rating: Derived rating score
    drs_rank: DRS category rank
    zrcs: Zwiftracing compound score
    source: Source of DRS (max30, max90, or none)
  """

  # Public attributes (in __init__)
  zwift_id: int = 0
  epoch: int = -1
  name: str = 'Nobody'
  gender: str = 'M'
  current_rating: float = 0.0
  current_rank: str = 'Unranked'
  max30_rating: float = 0.0
  max30_rank: str = 'Unranked'
  max90_rating: float = 0.0
  max90_rank: str = 'Unranked'
  drs_rating: float = 0.0
  drs_rank: str = 'Unranked'
  zrcs: float = 0.0
  source: str = 'none'

  # Private attributes (not in __init__)
  _raw: dict = field(default_factory=dict, init=False, repr=False)
  _rider: dict = field(default_factory=dict, init=False, repr=False)
  _verbose: bool = field(default=False, init=False, repr=False)
  _zr: AsyncZR_obj | None = field(default=None, init=False, repr=False)

  # -----------------------------------------------------------------------
  def set_session(self, zr: AsyncZR_obj) -> None:
    """Set the AsyncZR_obj session to use for async fetching.

    Args:
      zr: AsyncZR_obj instance to use for API requests
    """
    self._zr = zr

  # -----------------------------------------------------------------------
  def fetch(self, zwift_id: int | None = None, epoch: int | None = None) -> None:
    """Fetch rider rating data from the Zwiftracing API (synchronous).

    Fetches the rider's current or historical rating data based on the
    provided zwift_id and optional epoch (unix timestamp).

    Args:
      zwift_id: Rider's Zwift ID (uses self.zwift_id if not provided)
      epoch: Unix timestamp for historical data (uses self.epoch if not provided)

    Raises:
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      rider = ZRRider()
      rider.fetch(zwift_id=12345)
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
      f'Fetching rider for zwift_id={self.zwift_id}, epoch={self.epoch}',
    )

    # Build endpoint
    if self.epoch >= 0:
      endpoint = f'/public/riders/{self.zwift_id}/{self.epoch}'
    else:
      endpoint = f'/public/riders/{self.zwift_id}'

    # Fetch JSON from API
    headers = {'Authorization': config.authorization}
    try:
      self._raw = self.fetch_json(endpoint, headers=headers)
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch rider: {e}')
      raise

    # Parse response
    self._parse_response()

  # -----------------------------------------------------------------------
  async def afetch(
    self,
    zwift_id: int | None = None,
    epoch: int | None = None,
  ) -> None:
    """Fetch rider rating data from the Zwiftracing API (asynchronous).

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
      rider = ZRRider()
      rider.set_session(zr)
      await rider.afetch(zwift_id=12345)
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

  # -----------------------------------------------------------------------
  def _parse_response(self) -> None:
    """Parse API response into object attributes.

    Extracts rider information from the raw API response and populates
    the object's attributes. Silently uses defaults if fields are missing.
    """
    if not self._raw:
      logger.warning('No data to parse')
      return

    self._rider = self._raw

    # Check for error in response
    if 'message' in self._rider:
      logger.error(f"API error: {self._rider['message']}")
      return

    # Check for required fields
    if 'name' not in self._rider or 'race' not in self._rider:
      logger.warning('Missing required fields (name or race) in response')
      return

    try:
      self.name = self._rider.get('name', 'Nobody')
      self.gender = self._rider.get('gender', 'M')

      # ZRCS (compound score)
      power = self._rider.get('power', {})
      self.zrcs = power.get('compoundScore', 0.0)

      # Current rating
      race = self._rider.get('race', {})
      current = race.get('current', {})
      self.current_rating = current.get('rating', 0.0)
      current_mixed = current.get('mixed', {})
      self.current_rank = current_mixed.get('category', 'Unranked')

      # Max90 rating
      max90 = race.get('max90', {})
      max90_rating = max90.get('rating')
      if max90_rating is not None:
        self.max90_rating = max90_rating
      max90_mixed = max90.get('mixed', {})
      self.max90_rank = max90_mixed.get('category', 'Unranked')

      # Max30 rating
      max30 = race.get('max30', {})
      max30_rating = max30.get('rating')
      if max30_rating is not None:
        self.max30_rating = max30_rating
      max30_mixed = max30.get('mixed', {})
      self.max30_rank = max30_mixed.get('category', 'Unranked')

      # Determine DRS (derived rating score)
      if self.max30_rank != 'Unranked':
        self.drs_rating = self.max30_rating
        self.drs_rank = self.max30_rank
        self.source = 'max30'
      elif self.max90_rank != 'Unranked':
        self.drs_rating = self.max90_rating
        self.drs_rank = self.max90_rank
        self.source = 'max90'

      logger.debug(
        f'Successfully parsed rider {self.name} (zwift_id={self.zwift_id})',
      )
    except (KeyError, TypeError) as e:
      logger.error(f'Error parsing response: {e}')

  # -----------------------------------------------------------------------
  @staticmethod
  def fetch_batch(
    *zwift_ids: int,
    epoch: int | None = None,
  ) -> dict[int, 'ZRRider']:
    """Fetch multiple riders in a single request (POST, synchronous).

    Uses the Zwiftracing API batch endpoint to fetch current or historical
    data for multiple riders in a single request. More efficient than
    individual GET requests.

    Args:
      *zwift_ids: Rider IDs to fetch (max 1000 per request)
      epoch: Unix timestamp for historical data (None for current)

    Returns:
      Dictionary mapping rider ID to ZRRider instance with parsed data

    Raises:
      ValueError: If more than 1000 IDs provided
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      riders = ZRRider.fetch_batch(12345, 67890, 11111)
      for zwift_id, rider in riders.items():
        print(f"{rider.name}: {rider.current_rating}")

      # Historical data
      riders = ZRRider.fetch_batch(12345, 67890, epoch=1704067200)
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

    logger.debug(f'Fetching batch of {len(zwift_ids)} riders, epoch={epoch}')

    # Build endpoint
    if epoch is not None:
      endpoint = f'/public/riders/{epoch}'
    else:
      endpoint = '/public/riders'

    # Fetch JSON from API using POST
    headers = {'Authorization': config.authorization}
    try:
      rider_obj = ZRRider()
      raw_data = rider_obj.fetch_json(
        endpoint,
        headers=headers,
        json=list(zwift_ids),
        method='POST',
      )
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch batch: {e}')
      raise

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
        logger.debug(f'Parsed batch rider: {rider.name} (zwift_id={rider.zwift_id})')
      except (KeyError, TypeError) as e:
        logger.warning(f'Skipping malformed rider in batch response: {e}')
        continue

    logger.info(
      f'Successfully fetched {len(results)}/{len(zwift_ids)} riders in batch',
    )
    return results

  # -----------------------------------------------------------------------
  @staticmethod
  async def afetch_batch(
    *zwift_ids: int,
    epoch: int | None = None,
    zr: AsyncZR_obj | None = None,
  ) -> dict[int, 'ZRRider']:
    """Fetch multiple riders in a single request (POST, asynchronous).

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
        riders = await ZRRider.afetch_batch(12345, 67890, 11111, zr=zr)
        for zwift_id, rider in riders.items():
          print(f"{rider.name}: {rider.current_rating}")

      # Without session (creates temporary)
      riders = await ZRRider.afetch_batch(12345, 67890)

      # Historical data
      riders = await ZRRider.afetch_batch(12345, 67890, epoch=1704067200, zr=zr)
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

  # -----------------------------------------------------------------------
  def to_dict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with all public attributes
    """
    return {k: v for k, v in asdict(self).items() if not k.startswith('_')}
