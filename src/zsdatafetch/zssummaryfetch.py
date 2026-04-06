"""Fetcher class for Zwift Status summary and components data."""

import asyncio
import json

from shared.exceptions import NetworkError
from shared.json_helpers import parse_json_safe
from zsdatafetch.async_zs import AsyncZS_obj
from zsdatafetch.logging_config import get_logger
from zsdatafetch.models.component import ZSComponent
from zsdatafetch.models.page import ZSPage
from zsdatafetch.models.summary import ZSSummary
from zsdatafetch.zs import ZS_obj

logger = get_logger(__name__)


class ZSSummaryFetch(ZS_obj):
  """Fetches summary or components data from the Zwift Status API.

  Synchronous usage:
    fetcher = ZSSummaryFetch()
    summary = fetcher.fetch()
    print(summary.status.description)

  Components only:
    fetcher = ZSSummaryFetch()
    summary = fetcher.fetch(components_only=True)
    for comp in summary.components:
      print(f"{comp.name}: {comp.status}")

  Asynchronous usage:
    async with AsyncZS_obj() as zs:
      fetcher = ZSSummaryFetch()
      fetcher.set_session(zs)
      summary = await fetcher.afetch()
  """

  _sync_mode: bool = False

  def __init__(self) -> None:
    """Initialize ZSSummaryFetch."""
    self._fetched: ZSSummary | None = None
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
    self, components_only: bool = False,
  ) -> ZSSummary:
    """Fetch summary or components data (synchronous).

    Args:
      components_only: If True, fetch /components.json only

    Returns:
      ZSSummary with parsed data

    Raises:
      NetworkError: If the request fails
    """
    if self._sync_mode:
      return self._fetch_sync(components_only=components_only)

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
          components_only=components_only,
        ),
      )

  async def afetch(
    self, components_only: bool = False,
  ) -> ZSSummary:
    """Fetch summary or components data (asynchronous).

    Args:
      components_only: If True, fetch /components.json only

    Returns:
      ZSSummary with parsed data
    """
    return await self._afetch_internal(
      components_only=components_only,
    )

  def _fetch_sync(
    self, components_only: bool = False,
  ) -> ZSSummary:
    """Synchronous fetch implementation."""
    endpoint = (
      '/components.json' if components_only
      else '/summary.json'
    )
    logger.debug(f'Fetching {endpoint} (sync)')

    try:
      raw_json = self.fetch_json(endpoint)
      self._raw = raw_json

      parsed = parse_json_safe(raw_json, context='summary')
      if not isinstance(parsed, dict):
        logger.error('Expected dict for summary data')
        return ZSSummary()

      if components_only:
        summary = ZSSummary(
          page=ZSPage.from_dict(parsed.get('page', {})),
          components=[
            ZSComponent.from_dict(c)
            for c in parsed.get('components', [])
            if isinstance(c, dict)
          ],
        )
      else:
        summary = ZSSummary.from_dict(parsed)

      self._fetched = summary
      logger.info(f'Successfully fetched {endpoint}')
      return summary
    except NetworkError:
      raise

  async def _afetch_internal(
    self, components_only: bool = False,
  ) -> ZSSummary:
    """Internal async fetch implementation."""
    endpoint = (
      '/components.json' if components_only
      else '/summary.json'
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

      parsed = parse_json_safe(raw_json, context='summary')
      if not isinstance(parsed, dict):
        logger.error('Expected dict for summary data')
        return ZSSummary()

      if components_only:
        summary = ZSSummary(
          page=ZSPage.from_dict(parsed.get('page', {})),
          components=[
            ZSComponent.from_dict(c)
            for c in parsed.get('components', [])
            if isinstance(c, dict)
          ],
        )
      else:
        summary = ZSSummary.from_dict(parsed)

      self._fetched = summary
      logger.info(f'Successfully fetched {endpoint}')
      return summary
    except NetworkError:
      raise
    finally:
      if owns_session:
        await session.close()

  def raw(self) -> str:
    """Return the raw response string."""
    return self._raw

  def fetched(self) -> ZSSummary | None:
    """Return the fetched ZSSummary object."""
    return self._fetched

  def json(self) -> str:
    """Serialize fetched data to JSON string."""
    if self._fetched is None:
      return '{}'
    return json.dumps(self._fetched.asdict(), indent=2)
