"""Unified ZRRider class with both sync and async fetch capabilities.

This module provides the ZRRider class for fetching and storing rider
rating data from the Zwiftracing API.
"""

import asyncio
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
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
  _raw: str = field(default='', init=False, repr=False)
  _rider: dict = field(default_factory=dict, init=False, repr=False)
  _verbose: bool = field(default=False, init=False, repr=False)
  _zr: AsyncZR_obj | None = field(default=None, init=False, repr=False)
  _zr_sync: ZR_obj | None = field(default=None, init=False, repr=False)

  # -----------------------------------------------------------------------
  def set_session(self, zr: AsyncZR_obj) -> None:
    """Set the AsyncZR_obj session to use for async fetching.

    Args:
      zr: AsyncZR_obj instance to use for API requests
    """
    self._zr = zr

  # -----------------------------------------------------------------------
  def set_zr_session(self, zr: ZR_obj) -> None:
    """Set the ZR_obj session to use for fetching.

    Session will be converted to async for internal use.

    Args:
      zr: ZR_obj instance to use for API requests
    """
    self._zr_sync = zr

  # -----------------------------------------------------------------------
  async def _get_or_create_session(self) -> tuple[AsyncZR_obj, bool]:
    """Get or create an async session for fetching.

    Returns:
      Tuple of (AsyncZR_obj session, owns_session flag)
      If owns_session is True, caller must close the session
    """
    # Case 1: Use existing async session
    if self._zr:
      return (self._zr, False)

    # Case 2: Have sync session - create new async session
    if self._zr_sync:
      async_zr = AsyncZR_obj()
      await async_zr.init_client()
      return (async_zr, True)

    # Case 3: Create temporary session
    temp_zr = AsyncZR_obj()
    await temp_zr.init_client()
    return (temp_zr, True)

  # -----------------------------------------------------------------------
  async def _afetch_internal(
    self,
    zwift_id: int | None = None,
    epoch: int | None = None,
  ) -> None:
    """Internal async fetch implementation.

    Args:
      zwift_id: Rider's Zwift ID (uses self.zwift_id if not provided)
      epoch: Unix timestamp for historical data (uses self.epoch if not provided)
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
      raise ConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    session, owns_session = await self._get_or_create_session()

    try:
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
      self._raw = await session.fetch_json(endpoint, headers=headers)

      # Parse response
      self._parse_response()
      logger.info(
        f'Successfully fetched rider {self.name} (zwift_id={self.zwift_id})',
      )
    except NetworkError as e:
      logger.error(f'Failed to fetch rider: {e}')
      raise
    finally:
      if owns_session:
        await session.close()

  # -----------------------------------------------------------------------
  def fetch(self, zwift_id: int | None = None, epoch: int | None = None) -> None:
    """Fetch rider rating data from the Zwiftracing API (synchronous interface).

    Uses async implementation internally for consistency and efficiency.
    Fetches the rider's current or historical rating data based on the
    provided zwift_id and optional epoch (unix timestamp).

    Args:
      zwift_id: Rider's Zwift ID (uses self.zwift_id if not provided)
      epoch: Unix timestamp for historical data (uses self.epoch if not provided)

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured
      RuntimeError: If called from async context (use afetch() instead)

    Example:
      rider = ZRRider()
      rider.fetch(zwift_id=12345)
      print(rider.json())
    """
    try:
      asyncio.get_running_loop()
      raise RuntimeError(
        'fetch() called from async context. Use afetch() instead, or '
        'call fetch() from synchronous code.',
      )
    except RuntimeError as e:
      if 'fetch() called from async context' in str(e):
        raise
      # No running loop - safe to use asyncio.run()
      asyncio.run(self._afetch_internal(zwift_id, epoch))

  # -----------------------------------------------------------------------
  async def afetch(
    self,
    zwift_id: int | None = None,
    epoch: int | None = None,
  ) -> None:
    """Fetch rider rating data from the Zwiftracing API (asynchronous interface).

    Uses shared internal async implementation. Supports session sharing
    via set_session() or set_zr_session().

    Args:
      zwift_id: Rider's Zwift ID (uses self.zwift_id if not provided)
      epoch: Unix timestamp for historical data (uses self.epoch if not provided)

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured

    Example:
      rider = ZRRider()
      rider.set_session(zr)
      await rider.afetch(zwift_id=12345)
      print(rider.json())
    """
    await self._afetch_internal(zwift_id, epoch)

  # -----------------------------------------------------------------------
  def _parse_response(self) -> None:
    """Parse API response into object attributes.

    Extracts rider information from the raw API response and populates
    the object's attributes. Silently uses defaults if fields are missing.
    """
    if not self._raw:
      logger.warning('No data to parse')
      return

    # Parse JSON string to dict
    parsed = parse_json_safe(self._raw, context=f'rider {self.zwift_id}')
    if not isinstance(parsed, dict):
      logger.error(f'Expected dict for rider data, got {type(parsed).__name__}')
      return

    self._rider = parsed

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
    zr: ZR_obj | None = None,
  ) -> dict[int, 'ZRRider']:
    """Fetch multiple riders in a single request (POST, synchronous).

    Uses the Zwiftracing API batch endpoint to fetch current or historical
    data for multiple riders in a single request. More efficient than
    individual GET requests.

    Args:
      *zwift_ids: Rider IDs to fetch (max 1000 per request)
      epoch: Unix timestamp for historical data (None for current)
      zr: Optional ZR_obj session. If not provided, creates temporary instance.

    Returns:
      Dictionary mapping rider ID to ZRRider instance with parsed data

    Raises:
      ValueError: If more than 1000 IDs provided
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured

    Example:
      # With session
      zr = ZR_obj()
      riders = ZRRider.fetch_batch(12345, 67890, 11111, zr=zr)
      for zwift_id, rider in riders.items():
        print(f"{rider.name}: {rider.current_rating}")

      # Without session (creates temporary)
      riders = ZRRider.fetch_batch(12345, 67890)

      # Historical data
      riders = ZRRider.fetch_batch(12345, 67890, epoch=1704067200, zr=zr)
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
      raise ConfigError(
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
      # Use provided session or create temporary instance
      if zr is not None:
        logger.debug('Using provided ZR session for batch fetch')
        raw_data = zr.fetch_json(
          endpoint,
          headers=headers,
          json=list(zwift_ids),
          method='POST',
        )
      else:
        logger.debug('Creating temporary ZR instance for batch fetch')
        rider_obj = ZRRider()
        raw_data = rider_obj.fetch_json(
          endpoint,
          headers=headers,
          json=list(zwift_ids),
          method='POST',
        )
    except NetworkError as e:
      logger.error(f'Failed to fetch batch: {e}')
      raise

    # Parse response into individual ZRRider objects
    results = {}

    # Parse the raw string to get list of rider dicts
    parsed = parse_json_safe(raw_data, context='batch riders')
    if not isinstance(parsed, list):
      logger.error('Expected list of riders in batch response')
      return results

    for rider_data in parsed:
      try:
        rider = ZRRider()
        # Convert dict back to JSON string for storage in _raw
        rider._raw = json.dumps(rider_data)
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
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured

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
      raise ConfigError(
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

      # Parse the raw string to get list of rider dicts
      parsed = parse_json_safe(raw_data, context='batch riders (async)')
      if not isinstance(parsed, list):
        logger.error('Expected list of riders in batch response')
        return results

      for rider_data in parsed:
        try:
          rider = ZRRider()
          # Convert dict back to JSON string for storage in _raw
          rider._raw = json.dumps(rider_data)
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

    except NetworkError as e:
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
