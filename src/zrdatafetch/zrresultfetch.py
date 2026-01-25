"""Fetcher class for Zwiftracing race result data.

This module provides the ZRResultFetch class for fetching race results
from the Zwiftracing API. Returns native ZRRaceResult dataclass objects.
"""

import asyncio
import json

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrraceresult import ZRRaceResult

logger = get_logger(__name__)


class ZRResultFetch(ZR_obj):
  """Fetches race result data from Zwiftracing API.

  Returns native ZRRaceResult dataclass objects instead of raw dicts.
  Supports both synchronous and asynchronous operations.

  Synchronous usage:
    fetcher = ZRResultFetch()
    results = fetcher.fetch(3590800, 3590801)
    for race_id, result in results.items():
      print(f"{result.event_title}: {len(result)} riders")

  Asynchronous usage:
    async with AsyncZR_obj() as zr:
      fetcher = ZRResultFetch()
      fetcher.set_session(zr)
      results = await fetcher.afetch(3590800)

  Attributes:
    _fetched: Dictionary mapping race IDs to ZRRaceResult objects
    _raw: Dictionary mapping race IDs to raw JSON strings
  """

  _sync_mode: bool = False

  def __init__(self) -> None:
    """Initialize a new ZRResultFetch instance."""
    super().__init__()
    self._fetched: dict[int, ZRRaceResult] = {}
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
  async def _afetch_internal(self, *race_ids: int) -> dict[int, ZRRaceResult]:
    """Internal async fetch implementation.

    Args:
      *race_ids: One or more race IDs to fetch

    Returns:
      Dictionary mapping race IDs to ZRRaceResult objects
    """
    if not race_ids:
      logger.warning('No race_ids provided for fetch')
      return {}

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config".',
      )

    session, owns_session = await self._get_or_create_session()

    try:
      results: dict[int, ZRRaceResult] = {}
      raw_results: dict[int, str] = {}

      for race_id in race_ids:
        logger.debug(f'Fetching results for race_id={race_id}')

        # Endpoint is /public/results/{race_id}
        endpoint = f'/public/results/{race_id}'

        # Fetch JSON from API
        headers = {'Authorization': config.authorization}
        raw_json = await session.fetch_json(endpoint, headers=headers)
        raw_results[race_id] = raw_json

        # Parse response and create ZRRaceResult object
        parsed = parse_json_safe(raw_json, context=f'race result {race_id}')
        if isinstance(parsed, dict):
          # Ensure race_id is in the dict (inject if missing)
          if 'eventId' not in parsed:
            parsed['eventId'] = race_id
          result = ZRRaceResult.from_dict(parsed)
          # Ensure race_id is set correctly
          if result.race_id == 0:
            result = ZRRaceResult(
              race_id=race_id,
              event_title=result.event_title,
              event_time=result.event_time,
              route_id=result.route_id,
              distance=result.distance,
              race_type=result.race_type,
              race_subtype=result.race_subtype,
            )
            result._results = parsed.get('results', [])
            result._excluded = result._excluded
            result._extra = result._extra

          results[race_id] = result
          logger.info(f'Successfully fetched results for race_id={race_id}')
        else:
          logger.error(
            f'Expected dict for result data, got {type(parsed).__name__}'
          )

      self._fetched = results
      self._raw = raw_results
      return results

    except NetworkError as e:
      logger.error(f'Failed to fetch race result(s): {e}')
      raise
    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  def _fetch_sync(self, *race_ids: int) -> dict[int, ZRRaceResult]:
    """Synchronous fetch implementation.

    Args:
      *race_ids: One or more race IDs to fetch

    Returns:
      Dictionary mapping race IDs to ZRRaceResult objects
    """
    logger.info(f'Fetching {len(race_ids)} result(s) in synchronous mode')

    if not race_ids:
      logger.warning('No race_ids provided for fetch')
      return {}

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config".',
      )

    zr = ZR_obj()

    try:
      results: dict[int, ZRRaceResult] = {}
      raw_results: dict[int, str] = {}

      for race_id in race_ids:
        logger.debug(f'Fetching results for race_id={race_id}')

        endpoint = f'/public/results/{race_id}'

        # Synchronous fetch
        headers = {'Authorization': config.authorization}
        raw_json = zr.fetch_json(endpoint, headers=headers)
        raw_results[race_id] = raw_json

        # Parse response and create ZRRaceResult object
        parsed = parse_json_safe(raw_json, context=f'race result {race_id}')
        if isinstance(parsed, dict):
          # Ensure race_id is in the dict
          if 'eventId' not in parsed:
            parsed['eventId'] = race_id
          result = ZRRaceResult.from_dict(parsed)
          results[race_id] = result
          logger.info(
            f'Successfully fetched results for race_id={race_id} in sync mode'
          )
        else:
          logger.error(
            f'Expected dict for result data, got {type(parsed).__name__}'
          )

      self._fetched = results
      self._raw = raw_results
      return results

    except NetworkError as e:
      logger.error(f'Failed to fetch race result(s): {e}')
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
    logger.info(f'ZRResultFetch mode set to: {mode}')

  # ----------------------------------------------------------------------------
  def fetch(self, *race_ids: int) -> dict[int, ZRRaceResult]:
    """Fetch race result data (synchronous interface).

    Args:
      *race_ids: One or more race IDs to fetch

    Returns:
      Dictionary mapping race IDs to ZRRaceResult objects

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured
      RuntimeError: If called from async context

    Example:
      fetcher = ZRResultFetch()
      results = fetcher.fetch(3590800, 3590801)
      for race_id, result in results.items():
        print(f"{result.event_title}: {len(result)} riders")
    """
    if self._sync_mode:
      return self._fetch_sync(*race_ids)

    try:
      asyncio.get_running_loop()
      raise RuntimeError(
        'fetch() called from async context. Use afetch() instead.',
      )
    except RuntimeError as e:
      if 'fetch() called from async context' in str(e):
        raise
      return asyncio.run(self._afetch_internal(*race_ids))

  # ----------------------------------------------------------------------------
  async def afetch(self, *race_ids: int) -> dict[int, ZRRaceResult]:
    """Fetch race result data (asynchronous interface).

    Args:
      *race_ids: One or more race IDs to fetch

    Returns:
      Dictionary mapping race IDs to ZRRaceResult objects

    Example:
      async with AsyncZR_obj() as zr:
        fetcher = ZRResultFetch()
        fetcher.set_session(zr)
        results = await fetcher.afetch(3590800)
    """
    return await self._afetch_internal(*race_ids)

  # ----------------------------------------------------------------------------
  def raw(self) -> dict[int, str]:
    """Return the raw response strings.

    Returns:
      Dictionary mapping race IDs to raw JSON strings
    """
    return self._raw

  # ----------------------------------------------------------------------------
  def fetched(self) -> dict[int, ZRRaceResult]:
    """Return the fetched ZRRaceResult objects.

    Returns:
      Dictionary mapping race IDs to ZRRaceResult objects
    """
    return self._fetched

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Serialize the fetched data to formatted JSON string.

    Returns:
      JSON string with 2-space indentation
    """
    serializable = {
      race_id: result.asdict() for race_id, result in self._fetched.items()
    }
    return json.dumps(serializable, indent=2)
