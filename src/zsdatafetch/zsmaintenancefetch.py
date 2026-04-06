"""Fetcher class for Zwift Status scheduled maintenance data."""

import asyncio
import json

from shared.exceptions import NetworkError
from shared.json_helpers import parse_json_safe
from zsdatafetch.async_zs import AsyncZS_obj
from zsdatafetch.logging_config import get_logger
from zsdatafetch.models.maintenance import ZSMaintenance
from zsdatafetch.zs import ZS_obj

logger = get_logger(__name__)


class ZSMaintenanceFetch(ZS_obj):
  """Fetches scheduled maintenance data from the Zwift Status API.

  Synchronous usage:
    fetcher = ZSMaintenanceFetch()
    maintenance = fetcher.fetch()

  Upcoming only:
    maintenance = fetcher.fetch(upcoming=True)

  Active only:
    maintenance = fetcher.fetch(active=True)

  Asynchronous usage:
    async with AsyncZS_obj() as zs:
      fetcher = ZSMaintenanceFetch()
      fetcher.set_session(zs)
      maintenance = await fetcher.afetch()
  """

  _sync_mode: bool = False

  def __init__(self) -> None:
    """Initialize ZSMaintenanceFetch."""
    self._fetched: list[ZSMaintenance] = []
    self._raw: str = ''
    self._zs: AsyncZS_obj | None = None

  def set_session(self, zs: AsyncZS_obj) -> None:
    """Set the AsyncZS_obj session for async fetching.

    Args:
      zs: AsyncZS_obj instance to use
    """
    self._zs = zs

  @classmethod
  def set_sync_mode(cls, enabled: bool) -> None:
    """Enable or disable synchronous fetch mode.

    Args:
      enabled: True for sync, False for async
    """
    cls._sync_mode = enabled

  def fetch(
    self,
    upcoming: bool = False,
    active: bool = False,
  ) -> list[ZSMaintenance]:
    """Fetch maintenance data (synchronous).

    Args:
      upcoming: If True, fetch upcoming maintenance only
      active: If True, fetch active maintenance only

    Returns:
      List of ZSMaintenance objects

    Raises:
      NetworkError: If the request fails
    """
    if self._sync_mode:
      return self._fetch_sync(
        upcoming=upcoming, active=active,
      )

    try:
      asyncio.get_running_loop()
      raise RuntimeError(
        'fetch() called from async context. '
        'Use afetch() instead.',
      )
    except RuntimeError as e:
      if 'fetch() called from async context' in str(e):
        raise
      return asyncio.run(
        self._afetch_internal(
          upcoming=upcoming, active=active,
        ),
      )

  async def afetch(
    self,
    upcoming: bool = False,
    active: bool = False,
  ) -> list[ZSMaintenance]:
    """Fetch maintenance data (asynchronous).

    Args:
      upcoming: If True, fetch upcoming maintenance only
      active: If True, fetch active maintenance only

    Returns:
      List of ZSMaintenance objects
    """
    return await self._afetch_internal(
      upcoming=upcoming, active=active,
    )

  @staticmethod
  def _get_endpoint(
    upcoming: bool = False,
    active: bool = False,
  ) -> str:
    """Determine the API endpoint based on flags.

    Args:
      upcoming: Fetch upcoming only
      active: Fetch active only

    Returns:
      API endpoint path
    """
    if upcoming:
      return '/scheduled-maintenances/upcoming.json'
    if active:
      return '/scheduled-maintenances/active.json'
    return '/scheduled-maintenances.json'

  def _fetch_sync(
    self,
    upcoming: bool = False,
    active: bool = False,
  ) -> list[ZSMaintenance]:
    """Synchronous fetch implementation."""
    endpoint = self._get_endpoint(
      upcoming=upcoming, active=active,
    )
    logger.debug(f'Fetching {endpoint} (sync)')

    try:
      raw_json = self.fetch_json(endpoint)
      self._raw = raw_json
      maintenance = self._parse_response(raw_json)
      self._fetched = maintenance
      logger.info(
        f'Fetched {len(maintenance)} maintenance window(s) '
        f'from {endpoint}',
      )
      return maintenance
    except NetworkError:
      raise

  async def _afetch_internal(
    self,
    upcoming: bool = False,
    active: bool = False,
  ) -> list[ZSMaintenance]:
    """Internal async fetch implementation."""
    endpoint = self._get_endpoint(
      upcoming=upcoming, active=active,
    )
    logger.debug(f'Fetching {endpoint} (async)')

    session = self._zs
    owns_session = False

    if session is None:
      session = AsyncZS_obj()
      await session.init_client()
      owns_session = True

    try:
      raw_json = await session.fetch_json(endpoint)
      self._raw = raw_json
      maintenance = self._parse_response(raw_json)
      self._fetched = maintenance
      logger.info(
        f'Fetched {len(maintenance)} maintenance window(s) '
        f'from {endpoint}',
      )
      return maintenance
    except NetworkError:
      raise
    finally:
      if owns_session:
        await session.close()

  @staticmethod
  def _parse_response(
    raw_json: str,
  ) -> list[ZSMaintenance]:
    """Parse JSON response into maintenance list.

    Args:
      raw_json: Raw JSON string from API

    Returns:
      List of ZSMaintenance objects
    """
    parsed = parse_json_safe(
      raw_json, context='maintenance',
    )
    if not isinstance(parsed, dict):
      logger.error('Expected dict for maintenance response')
      return []

    return [
      ZSMaintenance.from_dict(m)
      for m in parsed.get('scheduled_maintenances', [])
      if isinstance(m, dict)
    ]

  def raw(self) -> str:
    """Return the raw response string."""
    return self._raw

  def fetched(self) -> list[ZSMaintenance]:
    """Return the fetched ZSMaintenance objects."""
    return self._fetched

  def json(self) -> str:
    """Serialize fetched data to JSON string."""
    serializable = [m.asdict() for m in self._fetched]
    return json.dumps(serializable, indent=2)
