"""Fetcher class for Zwift Status incident data."""

import asyncio
import json

from shared.exceptions import NetworkError
from shared.json_helpers import parse_json_safe
from zsdatafetch.async_zs import AsyncZS_obj
from zsdatafetch.logging_config import get_logger
from zsdatafetch.models.incident import ZSIncident
from zsdatafetch.zs import ZS_obj

logger = get_logger(__name__)


class ZSIncidentFetch(ZS_obj):
  """Fetches incident data from the Zwift Status API.

  Synchronous usage:
    fetcher = ZSIncidentFetch()
    incidents = fetcher.fetch()

  Unresolved only:
    incidents = fetcher.fetch(unresolved_only=True)

  Asynchronous usage:
    async with AsyncZS_obj() as zs:
      fetcher = ZSIncidentFetch()
      fetcher.set_session(zs)
      incidents = await fetcher.afetch()
  """

  _sync_mode: bool = False

  def __init__(self) -> None:
    """Initialize ZSIncidentFetch."""
    self._fetched: list[ZSIncident] = []
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
    self, unresolved_only: bool = False,
  ) -> list[ZSIncident]:
    """Fetch incident data (synchronous).

    Args:
      unresolved_only: If True, fetch unresolved incidents only

    Returns:
      List of ZSIncident objects

    Raises:
      NetworkError: If the request fails
    """
    if self._sync_mode:
      return self._fetch_sync(
        unresolved_only=unresolved_only,
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
          unresolved_only=unresolved_only,
        ),
      )

  async def afetch(
    self, unresolved_only: bool = False,
  ) -> list[ZSIncident]:
    """Fetch incident data (asynchronous).

    Args:
      unresolved_only: If True, fetch unresolved incidents only

    Returns:
      List of ZSIncident objects
    """
    return await self._afetch_internal(
      unresolved_only=unresolved_only,
    )

  def _fetch_sync(
    self, unresolved_only: bool = False,
  ) -> list[ZSIncident]:
    """Synchronous fetch implementation."""
    endpoint = (
      '/incidents/unresolved.json' if unresolved_only
      else '/incidents.json'
    )
    logger.debug(f'Fetching {endpoint} (sync)')

    try:
      raw_json = self.fetch_json(endpoint)
      self._raw = raw_json
      incidents = self._parse_response(raw_json)
      self._fetched = incidents
      logger.info(
        f'Fetched {len(incidents)} incident(s) '
        f'from {endpoint}',
      )
      return incidents
    except NetworkError:
      raise

  async def _afetch_internal(
    self, unresolved_only: bool = False,
  ) -> list[ZSIncident]:
    """Internal async fetch implementation."""
    endpoint = (
      '/incidents/unresolved.json' if unresolved_only
      else '/incidents.json'
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
      incidents = self._parse_response(raw_json)
      self._fetched = incidents
      logger.info(
        f'Fetched {len(incidents)} incident(s) '
        f'from {endpoint}',
      )
      return incidents
    except NetworkError:
      raise
    finally:
      if owns_session:
        await session.close()

  @staticmethod
  def _parse_response(raw_json: str) -> list[ZSIncident]:
    """Parse JSON response into incident list.

    Args:
      raw_json: Raw JSON string from API

    Returns:
      List of ZSIncident objects
    """
    parsed = parse_json_safe(raw_json, context='incidents')
    if not isinstance(parsed, dict):
      logger.error('Expected dict for incidents response')
      return []

    return [
      ZSIncident.from_dict(i)
      for i in parsed.get('incidents', [])
      if isinstance(i, dict)
    ]

  def raw(self) -> str:
    """Return the raw response string."""
    return self._raw

  def fetched(self) -> list[ZSIncident]:
    """Return the fetched ZSIncident objects."""
    return self._fetched

  def json(self) -> str:
    """Serialize fetched data to JSON string."""
    serializable = [i.asdict() for i in self._fetched]
    return json.dumps(serializable, indent=2)
