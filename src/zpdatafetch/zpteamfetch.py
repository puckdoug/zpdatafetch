"""Unified Team class with both sync and async fetch capabilities."""

import asyncio
import json
from argparse import ArgumentParser
from collections.abc import Coroutine
from typing import Any

import anyio

from shared.json_helpers import parse_json_safe
from shared.validation import ValidationError, validate_id_list
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger, setup_logging
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj
from zpdatafetch.zpteam import ZPTeam

logger = get_logger(__name__)


# ==============================================================================
class ZPTeamFetch(ZP_obj):
  """Fetches and stores team roster data from Zwiftpower.

  Retrieves team member lists and associated rider information using
  team IDs. Supports both synchronous and asynchronous operations.

  Synchronous usage:
    team = ZPTeamFetch()
    team.fetch(123, 456)
    print(team.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      team = ZPTeamFetch()
      team.set_session(zp)
      await team.afetch(123, 456)
      print(team.json())

  Attributes:
    raw: Dictionary mapping team IDs to their roster data
    verbose: Enable verbose output for debugging
  """

  # Sync version
  _url: str = 'https://zwiftpower.com/cache3/teams/'
  _url_end: str = '_riders.json'

  # Async version uses different URL ending
  _url_end_async: str = '.json'
  _sync_mode: bool = False  # Class-level sync mode flag

  def __init__(self) -> None:
    """Initialize a new Team instance."""
    super().__init__()
    self._fetched: dict[int, ZPTeam] = {}  # Override type
    self._zp: AsyncZP | None = None  # Async session
    self._zp_sync: ZP | None = None  # Sync session (for reference only)

  # ----------------------------------------------------------------------------
  def set_session(self, zp: AsyncZP) -> None:
    """Set the AsyncZP session to use for async fetching.

    Args:
      zp: AsyncZP instance to use for API requests
    """
    self._zp = zp

  # ----------------------------------------------------------------------------
  def set_zp_session(self, zp: ZP) -> None:
    """Set the ZP session to use for fetching.

    Cookies from this session will be shared with async client.

    Args:
      zp: ZP instance to use for API requests
    """
    self._zp_sync = zp

  # ----------------------------------------------------------------------------
  async def _get_or_create_session(self) -> tuple[AsyncZP, bool]:
    """Get or create an async session for fetching.

    Returns:
      Tuple of (AsyncZP session, owns_session flag)
      If owns_session is True, caller must close the session
    """
    # Case 1: Use existing async session
    if self._zp:
      return (self._zp, False)

    # Case 2: Convert sync session to async by copying cookies
    if self._zp_sync:
      async_zp = AsyncZP(skip_credential_check=True)
      await async_zp.init_client()
      assert async_zp._client is not None
      assert self._zp_sync._client is not None
      async_zp._client.cookies = self._zp_sync._client.cookies
      return (async_zp, True)

    # Case 3: Create temporary session with login
    temp_zp = AsyncZP(skip_credential_check=True)
    await temp_zp.login()
    return (temp_zp, True)

  # ----------------------------------------------------------------------------
  async def _fetch_parallel(self, *team_id: int) -> dict[int, ZPTeam]:
    """Fetch team data in parallel using async requests.

    Args:
      *team_id: One or more team ID integers to fetch

    Returns:
      Dictionary mapping team IDs to their roster data
    """
    # SECURITY: Validate all team IDs before creating session
    # This avoids expensive login/session creation for invalid IDs
    try:
      validated_ids = validate_id_list(list(team_id), id_type='team')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching team data for {len(team_id)} ID(s)')

      # Build list of fetch tasks using correct URL ending
      fetch_tasks = []
      for tid in validated_ids:
        url = f'{self._url}{tid}{self._url_end}'
        fetch_tasks.append(session.fetch_json(url))

      # Execute all fetches in parallel

      results_raw: dict[int, str] = {}

      results_fetched: dict[int, ZPTeam] = {}

      async def fetch_and_store(
        idx: int,
        task: Coroutine[Any, Any, str],
      ) -> None:
        """Helper to fetch and store result."""
        try:
          raw_json = await task
          team_id = validated_ids[idx]
          results_raw[team_id] = raw_json

          # Parse for fetched dict
          parsed = parse_json_safe(raw_json, context=f'team {team_id}')
          team_dict = parsed if isinstance(parsed, dict) else {}
          results_fetched[team_id] = ZPTeam.from_dict(team_dict)

          logger.debug(f'Successfully fetched team ID: {team_id}')
        except Exception as e:
          logger.error(f'Failed to fetch team ID {validated_ids[idx]}: {e}')
          raise

      async with anyio.create_task_group() as tg:
        for idx, task in enumerate(fetch_tasks):
          tg.start_soon(fetch_and_store, idx, task)

      self._raw = results_raw
      self._fetched = results_fetched
      self.processed = {}  # Reserved for future use
      logger.info(f'Successfully fetched {len(validated_ids)} team roster(s)')

      return self._fetched

    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  def _fetch_sequential(self, *team_id: int) -> dict[int, ZPTeam]:
    """Fetch team data sequentially (synchronous mode).

    This method provides a clear, separate execution path for debugging.
    All requests are made synchronously in sequence, with no parallelization.

    Args:
      *team_id: One or more team ID integers to fetch

    Returns:
      Dictionary mapping team IDs to their data

    Raises:
      ValueError: If any ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    logger.info(
      f'Fetching team data in synchronous mode for {len(team_id)} ID(s)',
    )

    # SECURITY: Validate all IDs before processing
    try:
      validated_ids = validate_id_list(list(team_id), id_type='team')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    # Create synchronous ZP session
    zp = ZP()

    results_raw: dict[int, str] = {}
    results_fetched: dict[int, ZPTeam] = {}

    # Fetch each ID sequentially
    for id_val in validated_ids:
      logger.debug(f'Fetching team data for team ID: {id_val}')
      url = f'{self._url}{id_val}{self._url_end}'

      # Synchronous blocking call
      raw_json = zp.fetch_json(url)
      results_raw[id_val] = raw_json

      # Parse immediately (no parallel parsing)
      parsed = parse_json_safe(raw_json, context=f'team {id_val}')
      team_dict = parsed if isinstance(parsed, dict) else {}
      results_fetched[id_val] = ZPTeam.from_dict(team_dict)

      logger.debug(f'Successfully fetched team data for team ID: {id_val}')

    self._raw = results_raw

    self._fetched = results_fetched

    self.processed = {}  # Reserved for future use

    logger.info(
      f'Successfully fetched {len(validated_ids)} team(s) in sync mode',
    )
    return self._fetched

  @classmethod
  def set_sync_mode(cls, enabled: bool) -> None:
    """Enable or disable synchronous fetch mode.

    Args:
      enabled: True to enable sync mode, False for async (default)
    """
    cls._sync_mode = enabled
    mode = 'synchronous' if enabled else 'asynchronous (parallel)'
    logger.info(f'Team fetch mode set to: {mode}')

  def fetch(self, *team_id: int) -> dict[int, ZPTeam]:
    """Fetch team roster data for one or more team IDs (synchronous).

    Retrieves the complete list of team members from Zwiftpower cache.
    Stores results in the raw dictionary keyed by team ID.

    Args:
      *team_id: One or more team ID integers to fetch

    Returns:
      Dictionary mapping team IDs to their roster data

    Raises:
      ValueError: If any team ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    # Check if sync mode is enabled
    if self._sync_mode:
      return self._fetch_sequential(*team_id)

    # Default: use async parallel fetch
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
      return asyncio.run(self._fetch_parallel(*team_id))

  # ----------------------------------------------------------------------------
  async def afetch(self, *team_id: int) -> dict[int, ZPTeam]:
    """Fetch team data for one or more team IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Args:
      *team_id: One or more team ID integers to fetch

    Returns:
      Dictionary mapping team IDs to their data

    Raises:
      ValueError: If any team ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*team_id)

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Return JSON string representation of fetched data.

    Converts ZPTeam objects to dicts before serialization.

    Returns:
      JSON-formatted string of all fetched team data
    """
    serializable = {
      key: value.asdict() if isinstance(value, ZPTeam) else value
      for key, value in self._fetched.items()
    }
    return json.JSONEncoder(indent=2).encode(serializable)


# ==============================================================================
def main() -> None:
  p = ArgumentParser(
    description='Module for fetching cyclist data using the Zwiftpower API',
  )
  p.add_argument(
    '--verbose',
    '-v',
    action='count',
    default=0,
    help='increase output verbosity (-v for INFO, -vv for DEBUG)',
  )
  p.add_argument(
    '--raw',
    '-r',
    action='store_const',
    const=True,
    help='print all returned data',
  )
  p.add_argument('team_id', type=int, nargs='+', help='a list of team_ids')
  args = p.parse_args()

  # Configure logging based on verbosity level (output to stderr)
  if args.verbose >= 2:
    setup_logging(console_level='DEBUG', force_console=True)
  elif args.verbose == 1:
    setup_logging(console_level='INFO', force_console=True)

  x = ZPTeamFetch()

  x.fetch(*args.team_id)

  if args.raw:
    print(x.raw)


# ==============================================================================
if __name__ == '__main__':
  main()
