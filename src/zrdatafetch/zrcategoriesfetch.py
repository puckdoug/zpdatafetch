"""Fetcher class for Zwiftracing vELO2 category ranges.

This module provides the ZRCategoriesFetch class for fetching the vELO2
category ranges from the Zwiftracing API. Returns a native ZRCategories
dataclass object.
"""

import asyncio
import json

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrcategories import ZRCategories

logger = get_logger(__name__)


class ZRCategoriesFetch(ZR_obj):
  """Fetches vELO2 category ranges from the Zwiftracing API.

  Returns a native ZRCategories dataclass object instead of raw dicts.
  Supports both synchronous and asynchronous operations. Takes no IDs:
  the endpoint returns a single global response.

  Synchronous usage:
    fetcher = ZRCategoriesFetch()
    categories = fetcher.fetch()
    print(categories.scale)

  Asynchronous usage:
    async with AsyncZR_obj() as zr:
      fetcher = ZRCategoriesFetch()
      fetcher.set_session(zr)
      categories = await fetcher.afetch()

  Attributes:
    _fetched: Dictionary keyed 0 mapping to the ZRCategories object
    _raw: Dictionary keyed 0 mapping to the raw JSON string
  """

  _sync_mode: bool = False

  def __init__(self) -> None:
    """Initialize a new ZRCategoriesFetch instance."""
    super().__init__()
    self._fetched: dict[int, ZRCategories] = {}
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
  async def _afetch_internal(self) -> ZRCategories:
    """Internal async fetch implementation.

    Returns:
      ZRCategories object (empty if the response is not a dict)
    """
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
      logger.debug('Fetching vELO2 category ranges')

      # Endpoint is /v2/public/categories (relative to the base URL)
      endpoint = '/v2/public/categories'

      # Fetch JSON from API
      headers = {'Authorization': config.authorization}
      raw_json = await session.fetch_json(endpoint, headers=headers)

      # Parse response and create ZRCategories object
      parsed = parse_json_safe(raw_json, context='categories')
      if isinstance(parsed, dict):
        categories = ZRCategories.from_dict(parsed)
        logger.info('Successfully fetched vELO2 category ranges')
      else:
        logger.error(
          f'Expected dict for categories data, got {type(parsed).__name__}',
        )
        categories = ZRCategories()

      self._fetched = {0: categories}
      self._raw = {0: raw_json}
      return categories

    except NetworkError as e:
      logger.error(f'Failed to fetch category ranges: {e}')
      raise
    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  def _fetch_sync(self) -> ZRCategories:
    """Synchronous fetch implementation.

    Returns:
      ZRCategories object (empty if the response is not a dict)
    """
    logger.info('Fetching vELO2 category ranges in synchronous mode')

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
      endpoint = '/v2/public/categories'

      # Synchronous fetch
      headers = {'Authorization': config.authorization}
      raw_json = zr.fetch_json(endpoint, headers=headers)

      # Parse response and create ZRCategories object
      parsed = parse_json_safe(raw_json, context='categories')
      if isinstance(parsed, dict):
        categories = ZRCategories.from_dict(parsed)
        logger.info('Successfully fetched vELO2 category ranges in sync mode')
      else:
        logger.error(
          f'Expected dict for categories data, got {type(parsed).__name__}',
        )
        categories = ZRCategories()

      self._fetched = {0: categories}
      self._raw = {0: raw_json}
      return categories

    except NetworkError as e:
      logger.error(f'Failed to fetch category ranges: {e}')
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
    logger.info(f'ZRCategoriesFetch mode set to: {mode}')

  # ----------------------------------------------------------------------------
  def fetch(self) -> ZRCategories:
    """Fetch vELO2 category ranges (synchronous interface).

    Returns:
      ZRCategories object

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured
      RuntimeError: If called from async context

    Example:
      fetcher = ZRCategoriesFetch()
      categories = fetcher.fetch()
      print(categories.scale)
    """
    if self._sync_mode:
      return self._fetch_sync()

    try:
      asyncio.get_running_loop()
      raise RuntimeError(
        'fetch() called from async context. Use afetch() instead.',
      )
    except RuntimeError as e:
      if 'fetch() called from async context' in str(e):
        raise
      return asyncio.run(self._afetch_internal())

  # ----------------------------------------------------------------------------
  async def afetch(self) -> ZRCategories:
    """Fetch vELO2 category ranges (asynchronous interface).

    Returns:
      ZRCategories object

    Example:
      async with AsyncZR_obj() as zr:
        fetcher = ZRCategoriesFetch()
        fetcher.set_session(zr)
        categories = await fetcher.afetch()
    """
    return await self._afetch_internal()

  # ----------------------------------------------------------------------------
  def raw(self) -> dict[int, str]:
    """Return the raw response strings.

    Returns:
      Dictionary keyed 0 mapping to the raw JSON string
    """
    return self._raw

  # ----------------------------------------------------------------------------
  def fetched(self) -> dict[int, ZRCategories]:
    """Return the fetched ZRCategories objects.

    Returns:
      Dictionary keyed 0 mapping to the ZRCategories object
    """
    return self._fetched

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Serialize the fetched data to formatted JSON string.

    Returns:
      JSON string with 2-space indentation
    """
    serializable = {key: obj.asdict() for key, obj in self._fetched.items()}
    return json.dumps(serializable, indent=2)
