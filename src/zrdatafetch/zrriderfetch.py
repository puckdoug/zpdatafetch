"""Fetcher class for Zwiftracing rider rating data.

This module provides the ZRRiderFetch class for fetching rider rating data
from the Zwiftracing API. Returns native ZRRider dataclass objects.
"""

import asyncio
import json

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrrider import ZRRider

logger = get_logger(__name__)


class ZRRiderFetch(ZR_obj):
  """Fetches rider rating data from Zwiftracing API.

  Returns native ZRRider dataclass objects instead of raw dicts.
  Supports both synchronous and asynchronous operations.

  Synchronous usage:
    fetcher = ZRRiderFetch()
    riders = fetcher.fetch(12345, 67890)
    for zwift_id, rider in riders.items():
      print(f"{rider.name}: {rider.current_rating}")

  Asynchronous usage:
    async with AsyncZR_obj() as zr:
      fetcher = ZRRiderFetch()
      fetcher.set_session(zr)
      riders = await fetcher.afetch(12345, 67890)

  Batch fetching:
    riders = ZRRiderFetch.fetch_batch(12345, 67890, 11111)

  Attributes:
    _fetched: Dictionary mapping zwift IDs to ZRRider objects
    _raw: Dictionary mapping zwift IDs to raw JSON strings
  """

  _sync_mode: bool = False  # Class-level sync mode flag

  def __init__(self) -> None:
    """Initialize a new ZRRiderFetch instance."""
    super().__init__()
    self._fetched: dict[int, ZRRider] = {}
    self._raw: dict[int, str] = {}
    self._zr: AsyncZR_obj | None = None
    self._zr_sync: ZR_obj | None = None

  # ----------------------------------------------------------------------------
  def set_session(self, zr: AsyncZR_obj) -> None:
    """Set the AsyncZR_obj session to use for async fetching.

    Args:
      zr: AsyncZR_obj instance to use for API requests
    """
    self._zr = zr

  # ----------------------------------------------------------------------------
  def set_zr_session(self, zr: ZR_obj) -> None:
    """Set the ZR_obj session to use for fetching.

    Args:
      zr: ZR_obj instance to use for API requests
    """
    self._zr_sync = zr

  # ----------------------------------------------------------------------------
  async def _get_or_create_session(self) -> tuple[AsyncZR_obj, bool]:
    """Get or create an async session for fetching.

    Returns:
      Tuple of (AsyncZR_obj session, owns_session flag)
    """
    if self._zr:
      return (self._zr, False)

    if self._zr_sync:
      async_zr = AsyncZR_obj()
      await async_zr.init_client()
      return (async_zr, True)

    temp_zr = AsyncZR_obj()
    await temp_zr.init_client()
    return (temp_zr, True)

  # ----------------------------------------------------------------------------
  async def _afetch_internal(
    self,
    *zwift_ids: int,
    epoch: int | None = None,
  ) -> dict[int, ZRRider]:
    """Internal async fetch implementation.

    Args:
      *zwift_ids: One or more Zwift IDs to fetch
      epoch: Unix timestamp for historical data (None for current)

    Returns:
      Dictionary mapping zwift IDs to ZRRider objects
    """
    if not zwift_ids:
      logger.warning('No zwift_ids provided for fetch')
      return {}

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ConfigError(
        'Zwiftracing authorization not found. '
        'Please run "zrdata config" to set it up.',
      )

    session, owns_session = await self._get_or_create_session()

    try:
      results: dict[int, ZRRider] = {}
      raw_results: dict[int, str] = {}

      for zwift_id in zwift_ids:
        logger.debug(f'Fetching rider for zwift_id={zwift_id}, epoch={epoch}')

        # Build endpoint
        if epoch is not None and epoch >= 0:
          endpoint = f'/public/riders/{zwift_id}/{epoch}'
        else:
          endpoint = f'/public/riders/{zwift_id}'

        # Fetch JSON from API
        headers = {'Authorization': config.authorization}
        raw_json = await session.fetch_json(endpoint, headers=headers)
        raw_results[zwift_id] = raw_json

        # Parse response and create ZRRider object
        parsed = parse_json_safe(raw_json, context=f'rider {zwift_id}')
        if isinstance(parsed, dict):
          rider = ZRRider.from_dict(parsed)
          # Ensure zwift_id is set (in case API doesn't return it)
          if rider.zwift_id == 0:
            rider = ZRRider(
              zwift_id=zwift_id,
              name=rider.name,
              gender=rider.gender,
              current_rating=rider.current_rating,
              current_rank=rider.current_rank,
              max30_rating=rider.max30_rating,
              max30_rank=rider.max30_rank,
              max90_rating=rider.max90_rating,
              max90_rank=rider.max90_rank,
              zrcs=rider.zrcs,
              _excluded=rider._excluded,
              _extra=rider._extra,
            )
          results[zwift_id] = rider
          logger.info(
            f'Successfully fetched rider {rider.name} (zwift_id={zwift_id})',
          )
        else:
          logger.error(
            f'Expected dict for rider data, got {type(parsed).__name__}',
          )

      self._fetched = results
      self._raw = raw_results
      return results

    except NetworkError as e:
      logger.error(f'Failed to fetch rider(s): {e}')
      raise
    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  def _fetch_sync(
    self,
    *zwift_ids: int,
    epoch: int | None = None,
  ) -> dict[int, ZRRider]:
    """Synchronous fetch implementation.

    Args:
      *zwift_ids: One or more Zwift IDs to fetch
      epoch: Unix timestamp for historical data (None for current)

    Returns:
      Dictionary mapping zwift IDs to ZRRider objects
    """
    logger.info(f'Fetching {len(zwift_ids)} rider(s) in synchronous mode')

    if not zwift_ids:
      logger.warning('No zwift_ids provided for fetch')
      return {}

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ConfigError(
        'Zwiftracing authorization not found. '
        'Please run "zrdata config" to set it up.',
      )

    zr = ZR_obj()

    try:
      results: dict[int, ZRRider] = {}
      raw_results: dict[int, str] = {}

      for zwift_id in zwift_ids:
        logger.debug(f'Fetching rider for zwift_id={zwift_id}, epoch={epoch}')

        # Build endpoint
        if epoch is not None and epoch >= 0:
          endpoint = f'/public/riders/{zwift_id}/{epoch}'
        else:
          endpoint = f'/public/riders/{zwift_id}'

        # Synchronous fetch
        headers = {'Authorization': config.authorization}
        raw_json = zr.fetch_json(endpoint, headers=headers)
        raw_results[zwift_id] = raw_json

        # Parse response and create ZRRider object
        parsed = parse_json_safe(raw_json, context=f'rider {zwift_id}')
        if isinstance(parsed, dict):
          rider = ZRRider.from_dict(parsed)
          # Ensure zwift_id is set
          if rider.zwift_id == 0:
            rider = ZRRider(
              zwift_id=zwift_id,
              name=rider.name,
              gender=rider.gender,
              current_rating=rider.current_rating,
              current_rank=rider.current_rank,
              max30_rating=rider.max30_rating,
              max30_rank=rider.max30_rank,
              max90_rating=rider.max90_rating,
              max90_rank=rider.max90_rank,
              zrcs=rider.zrcs,
              _excluded=rider._excluded,
              _extra=rider._extra,
            )
          results[zwift_id] = rider
          logger.info(
            f'Successfully fetched rider (zwift_id={zwift_id}) in sync mode',
          )
        else:
          logger.error(
            f'Expected dict for rider data, got {type(parsed).__name__}',
          )

      self._fetched = results
      self._raw = raw_results
      return results

    except NetworkError as e:
      logger.error(f'Failed to fetch rider(s): {e}')
      raise

  # ----------------------------------------------------------------------------
  @classmethod
  def set_sync_mode(cls, enabled: bool) -> None:
    """Enable or disable synchronous fetch mode.

    Args:
      enabled: True to enable sync mode, False for async (default)
    """
    cls._sync_mode = enabled
    mode = 'synchronous' if enabled else 'asynchronous (parallel)'
    logger.info(f'ZRRiderFetch mode set to: {mode}')

  # ----------------------------------------------------------------------------
  def fetch(
    self,
    *zwift_ids: int,
    epoch: int | None = None,
  ) -> dict[int, ZRRider]:
    """Fetch rider rating data (synchronous interface).

    Args:
      *zwift_ids: One or more Zwift IDs to fetch
      epoch: Unix timestamp for historical data (None for current)

    Returns:
      Dictionary mapping zwift IDs to ZRRider objects

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured
      RuntimeError: If called from async context

    Example:
      fetcher = ZRRiderFetch()
      riders = fetcher.fetch(12345, 67890)
      for zwift_id, rider in riders.items():
        print(f"{rider.name}: {rider.current_rating}")
    """
    if self._sync_mode:
      return self._fetch_sync(*zwift_ids, epoch=epoch)

    try:
      asyncio.get_running_loop()
      raise RuntimeError(
        'fetch() called from async context. Use afetch() instead.',
      )
    except RuntimeError as e:
      if 'fetch() called from async context' in str(e):
        raise
      return asyncio.run(self._afetch_internal(*zwift_ids, epoch=epoch))

  # ----------------------------------------------------------------------------
  async def afetch(
    self,
    *zwift_ids: int,
    epoch: int | None = None,
  ) -> dict[int, ZRRider]:
    """Fetch rider rating data (asynchronous interface).

    Args:
      *zwift_ids: One or more Zwift IDs to fetch
      epoch: Unix timestamp for historical data (None for current)

    Returns:
      Dictionary mapping zwift IDs to ZRRider objects

    Example:
      async with AsyncZR_obj() as zr:
        fetcher = ZRRiderFetch()
        fetcher.set_session(zr)
        riders = await fetcher.afetch(12345, 67890)
    """
    return await self._afetch_internal(*zwift_ids, epoch=epoch)

  # ----------------------------------------------------------------------------
  @staticmethod
  def fetch_batch(
    *zwift_ids: int,
    epoch: int | None = None,
    zr: ZR_obj | None = None,
  ) -> dict[int, ZRRider]:
    """Fetch multiple riders in a single request (POST, synchronous).

    Uses the Zwiftracing API batch endpoint.

    Args:
      *zwift_ids: Rider IDs to fetch (max 1000 per request)
      epoch: Unix timestamp for historical data (None for current)
      zr: Optional ZR_obj session

    Returns:
      Dictionary mapping rider IDs to ZRRider objects

    Example:
      riders = ZRRiderFetch.fetch_batch(12345, 67890, 11111)
    """
    if len(zwift_ids) > 1000:
      raise ValueError('Maximum 1000 rider IDs per batch request')

    if len(zwift_ids) == 0:
      logger.warning('No rider IDs provided for batch fetch')
      return {}

    config = Config()
    config.load()
    if not config.authorization:
      raise ConfigError(
        'Zwiftracing authorization not found. '
        'Please run "zrdata config" to set it up.',
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
        temp_zr = ZR_obj()
        raw_data = temp_zr.fetch_json(
          endpoint,
          headers=headers,
          json=list(zwift_ids),
          method='POST',
        )
    except NetworkError as e:
      logger.error(f'Failed to fetch batch: {e}')
      raise

    # Parse response into ZRRider objects
    results: dict[int, ZRRider] = {}

    parsed = parse_json_safe(raw_data, context='batch riders')
    if not isinstance(parsed, list):
      logger.error('Expected list of riders in batch response')
      return results

    for rider_data in parsed:
      try:
        rider = ZRRider.from_dict(rider_data)
        results[rider.zwift_id] = rider
        logger.debug(
          f'Parsed batch rider: {rider.name} (zwift_id={rider.zwift_id})',
        )
      except (KeyError, TypeError) as e:
        logger.warning(f'Skipping malformed rider in batch response: {e}')
        continue

    logger.info(
      f'Successfully fetched {len(results)}/{len(zwift_ids)} riders in batch',
    )
    return results

  # ----------------------------------------------------------------------------
  @staticmethod
  async def afetch_batch(
    *zwift_ids: int,
    epoch: int | None = None,
    zr: AsyncZR_obj | None = None,
  ) -> dict[int, ZRRider]:
    """Fetch multiple riders in a single request (POST, asynchronous).

    Args:
      *zwift_ids: Rider IDs to fetch (max 1000 per request)
      epoch: Unix timestamp for historical data (None for current)
      zr: Optional AsyncZR_obj session

    Returns:
      Dictionary mapping rider IDs to ZRRider objects

    Example:
      async with AsyncZR_obj() as zr:
        riders = await ZRRiderFetch.afetch_batch(12345, 67890, zr=zr)
    """
    if len(zwift_ids) > 1000:
      raise ValueError('Maximum 1000 rider IDs per batch request')

    if len(zwift_ids) == 0:
      logger.warning('No rider IDs provided for batch fetch')
      return {}

    config = Config()
    config.load()
    if not config.authorization:
      raise ConfigError(
        'Zwiftracing authorization not found. '
        'Please run "zrdata config" to set it up.',
      )

    logger.debug(
      f'Fetching batch of {len(zwift_ids)} riders (async), epoch={epoch}',
    )

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

      # Parse response into ZRRider objects
      results: dict[int, ZRRider] = {}

      parsed = parse_json_safe(raw_data, context='batch riders (async)')
      if not isinstance(parsed, list):
        logger.error('Expected list of riders in batch response')
        return results

      for rider_data in parsed:
        try:
          rider = ZRRider.from_dict(rider_data)
          results[rider.zwift_id] = rider
          logger.debug(
            f'Parsed batch rider: {rider.name} (zwift_id={rider.zwift_id})',
          )
        except (KeyError, TypeError) as e:
          logger.warning(f'Skipping malformed rider in batch response: {e}')
          continue

      logger.info(
        f'Successfully fetched {len(results)}/{len(zwift_ids)} riders '
        f'in batch (async)',
      )
      return results

    except NetworkError as e:
      logger.error(f'Failed to fetch batch: {e}')
      raise
    finally:
      if owns_session and zr:
        await zr.close()

  # ----------------------------------------------------------------------------
  def raw(self) -> dict[int, str]:
    """Return the raw response strings.

    Returns:
      Dictionary mapping zwift IDs to raw JSON strings
    """
    return self._raw

  # ----------------------------------------------------------------------------
  def fetched(self) -> dict[int, ZRRider]:
    """Return the fetched ZRRider objects.

    Returns:
      Dictionary mapping zwift IDs to ZRRider objects
    """
    return self._fetched

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Serialize the fetched data to formatted JSON string.

    Returns:
      JSON string with 2-space indentation
    """
    serializable = {
      zwift_id: rider.asdict() for zwift_id, rider in self._fetched.items()
    }
    return json.dumps(serializable, indent=2)
