"""Fetcher class for Zwiftracing team roster data.

This module provides the ZRTeamFetch class for fetching team rosters
from the Zwiftracing API. Returns native ZRTeamRoster dataclass objects.
"""

import asyncio
import json

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrteamroster import ZRTeamRoster

logger = get_logger(__name__)


class ZRTeamFetch(ZR_obj):
  """Fetches team roster data from Zwiftracing API.

  Returns native ZRTeamRoster dataclass objects instead of raw dicts.
  Supports both synchronous and asynchronous operations.

  Synchronous usage:
    fetcher = ZRTeamFetch()
    teams = fetcher.fetch(456, 789)
    for team_id, roster in teams.items():
      print(f"{roster.team_name}: {len(roster)} members")

  Asynchronous usage:
    async with AsyncZR_obj() as zr:
      fetcher = ZRTeamFetch()
      fetcher.set_session(zr)
      teams = await fetcher.afetch(456)

  Attributes:
    _fetched: Dictionary mapping team IDs to ZRTeamRoster objects
    _raw: Dictionary mapping team IDs to raw JSON strings
  """

  _sync_mode: bool = False

  def __init__(self) -> None:
    """Initialize a new ZRTeamFetch instance."""
    super().__init__()
    self._fetched: dict[int, ZRTeamRoster] = {}
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
  async def _afetch_internal(self, *team_ids: int) -> dict[int, ZRTeamRoster]:
    """Internal async fetch implementation.

    Args:
      *team_ids: One or more team IDs to fetch

    Returns:
      Dictionary mapping team IDs to ZRTeamRoster objects
    """
    if not team_ids:
      logger.warning('No team_ids provided for fetch')
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
      results: dict[int, ZRTeamRoster] = {}
      raw_results: dict[int, str] = {}

      for team_id in team_ids:
        logger.debug(f'Fetching team roster for team_id={team_id}')

        # Endpoint is /public/clubs/{team_id}/0 (0 is starting rider offset)
        endpoint = f'/public/clubs/{team_id}/0'

        # Fetch JSON from API
        headers = {'Authorization': config.authorization}
        raw_json = await session.fetch_json(endpoint, headers=headers)
        raw_results[team_id] = raw_json

        # Parse response and create ZRTeamRoster object
        parsed = parse_json_safe(raw_json, context=f'team {team_id}')
        if isinstance(parsed, dict):
          roster = ZRTeamRoster.from_dict(parsed, team_id=team_id)
          results[team_id] = roster
          logger.info(f'Successfully fetched team roster for team_id={team_id}')
        else:
          logger.error(
            f'Expected dict for team data, got {type(parsed).__name__}',
          )

      self._fetched = results
      self._raw = raw_results
      return results

    except NetworkError as e:
      logger.error(f'Failed to fetch team roster(s): {e}')
      raise
    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  def _fetch_sync(self, *team_ids: int) -> dict[int, ZRTeamRoster]:
    """Synchronous fetch implementation.

    Args:
      *team_ids: One or more team IDs to fetch

    Returns:
      Dictionary mapping team IDs to ZRTeamRoster objects
    """
    logger.info(f'Fetching {len(team_ids)} team roster(s) in synchronous mode')

    if not team_ids:
      logger.warning('No team_ids provided for fetch')
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
      results: dict[int, ZRTeamRoster] = {}
      raw_results: dict[int, str] = {}

      for team_id in team_ids:
        logger.debug(f'Fetching team roster for team_id={team_id}')

        endpoint = f'/public/clubs/{team_id}/0'

        # Synchronous fetch
        headers = {'Authorization': config.authorization}
        raw_json = zr.fetch_json(endpoint, headers=headers)
        raw_results[team_id] = raw_json

        # Parse response and create ZRTeamRoster object
        parsed = parse_json_safe(raw_json, context=f'team {team_id}')
        if isinstance(parsed, dict):
          roster = ZRTeamRoster.from_dict(parsed, team_id=team_id)
          results[team_id] = roster
          logger.info(
            f'Successfully fetched team roster for team_id={team_id} '
            f'in sync mode',
          )
        else:
          logger.error(
            f'Expected dict for team data, got {type(parsed).__name__}',
          )

      self._fetched = results
      self._raw = raw_results
      return results

    except NetworkError as e:
      logger.error(f'Failed to fetch team roster(s): {e}')
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
    logger.info(f'ZRTeamFetch mode set to: {mode}')

  # ----------------------------------------------------------------------------
  def fetch(self, *team_ids: int) -> dict[int, ZRTeamRoster]:
    """Fetch team roster data (synchronous interface).

    Args:
      *team_ids: One or more team IDs to fetch

    Returns:
      Dictionary mapping team IDs to ZRTeamRoster objects

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured
      RuntimeError: If called from async context

    Example:
      fetcher = ZRTeamFetch()
      teams = fetcher.fetch(456, 789)
      for team_id, roster in teams.items():
        print(f"{roster.team_name}: {len(roster)} members")
    """
    if self._sync_mode:
      return self._fetch_sync(*team_ids)

    try:
      asyncio.get_running_loop()
      raise RuntimeError(
        'fetch() called from async context. Use afetch() instead.',
      )
    except RuntimeError as e:
      if 'fetch() called from async context' in str(e):
        raise
      return asyncio.run(self._afetch_internal(*team_ids))

  # ----------------------------------------------------------------------------
  async def afetch(self, *team_ids: int) -> dict[int, ZRTeamRoster]:
    """Fetch team roster data (asynchronous interface).

    Args:
      *team_ids: One or more team IDs to fetch

    Returns:
      Dictionary mapping team IDs to ZRTeamRoster objects

    Example:
      async with AsyncZR_obj() as zr:
        fetcher = ZRTeamFetch()
        fetcher.set_session(zr)
        teams = await fetcher.afetch(456)
    """
    return await self._afetch_internal(*team_ids)

  # ----------------------------------------------------------------------------
  def raw(self) -> dict[int, str]:
    """Return the raw response strings.

    Returns:
      Dictionary mapping team IDs to raw JSON strings
    """
    return self._raw

  # ----------------------------------------------------------------------------
  def fetched(self) -> dict[int, ZRTeamRoster]:
    """Return the fetched ZRTeamRoster objects.

    Returns:
      Dictionary mapping team IDs to ZRTeamRoster objects
    """
    return self._fetched

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Serialize the fetched data to formatted JSON string.

    Returns:
      JSON string with 2-space indentation
    """
    serializable = {
      team_id: roster.asdict() for team_id, roster in self._fetched.items()
    }
    return json.dumps(serializable, indent=2)
