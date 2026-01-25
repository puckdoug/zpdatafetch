"""Unified Cyclist class with both sync and async fetch capabilities."""

import asyncio
import json
import sys
from argparse import ArgumentParser
from collections.abc import Coroutine
from typing import Any

import anyio

# Python 3.10 compatibility
if sys.version_info >= (3, 11):
  from builtins import BaseExceptionGroup
else:
  # For Python 3.10, anyio provides ExceptionGroup
  try:
    from exceptiongroup import (  # type: ignore[import-untyped]
      BaseExceptionGroup,
    )
  except ImportError:
    # Fallback - catch the anyio exception type
    BaseExceptionGroup = Exception

from shared.json_helpers import parse_json_safe
from shared.validation import ValidationError, validate_id_list
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger, setup_logging
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj
from zpdatafetch.zpcyclist import ZPCyclist
from zpdatafetch.zpracelog import ZPRacelog

logger = get_logger(__name__)


# ==============================================================================
class ZPCyclistFetch(ZP_obj):
  """Fetches and stores cyclist profile data from Zwiftpower.

  Retrieves cyclist information including performance metrics, race history,
  and profile details using Zwift IDs. Supports both synchronous and
  asynchronous operations.

  Synchronous usage:
    cyclist = ZPCyclistFetch()
    cyclist.fetch(123456, 789012)
    print(cyclist.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      cyclist = ZPCyclistFetch()
      cyclist.set_session(zp)
      await cyclist.afetch(123456, 789012)
      print(cyclist.json())

  Attributes:
    raw: Dictionary mapping Zwift IDs to their profile data
    verbose: Enable verbose output for debugging
  """

  _url: str = 'https://zwiftpower.com/cache3/profile/'
  _profile: str = 'https://zwiftpower.com/profile.php?z='
  _url_end: str = '_all.json'
  _sync_mode: bool = False  # Class-level sync mode flag

  def __init__(self) -> None:
    """Initialize a new Cyclist instance."""
    super().__init__()
    self._fetched: dict[int, ZPCyclist] = {}  # Override type
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
  async def _fetch_parallel(self, *zwift_id: int) -> dict[int, ZPCyclist]:
    """Fetch cyclist data in parallel using async requests.

    Note: Only fetches JSON data, not profile pages.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to ZPCyclist objects
    """
    # SECURITY: Validate all Zwift IDs before creating session
    # This avoids expensive login/session creation for invalid IDs
    try:
      validated_ids = validate_id_list(list(zwift_id), id_type='zwift')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching cyclist data for {len(zwift_id)} ID(s)')

      # Build list of fetch tasks (JSON only, not profile pages)
      fetch_tasks = []
      for zid in validated_ids:
        url = f'{self._url}{zid}{self._url_end}'
        fetch_tasks.append(session.fetch_json(url))

      # Execute all fetches in parallel
      results_raw: dict[int, str] = {}
      results_fetched_dict: dict[
        int,
        dict[str, Any],
      ] = {}  # Temporary dict structure

      async def fetch_and_store(
        idx: int,
        task: Coroutine[Any, Any, str],
      ) -> None:
        """Helper to fetch and store result."""
        zid = validated_ids[idx]
        try:
          raw_json = await task
          results_raw[zid] = raw_json

          # Parse for fetched dict
          parsed = parse_json_safe(raw_json, context=f'cyclist {zid}')
          results_fetched_dict[zid] = parsed if isinstance(parsed, dict) else {}

          logger.debug(
            f'Successfully fetched profile for Zwift ID: {zid}',
          )
        except Exception as e:
          logger.debug(f'Failed to fetch Zwift ID {zid}: {e}')
          # Re-raise with Zwift ID in message for better error context
          from shared.exceptions import NetworkError

          if isinstance(e, NetworkError):
            # Extract the original error message and add Zwift ID context
            error_msg = str(e)
            if 'Failed to fetch Zwift profile' in error_msg:
              # Replace generic message with ID-specific one
              error_msg = error_msg.replace(
                'Failed to fetch Zwift profile',
                f'Failed to fetch Zwift ID {zid}',
              )
              raise NetworkError(error_msg) from e
          raise

      try:
        async with anyio.create_task_group() as tg:
          for idx, task in enumerate(fetch_tasks):
            tg.start_soon(fetch_and_store, idx, task)
      except BaseExceptionGroup as eg:
        # Extract the first NetworkError from the exception group
        from shared.exceptions import NetworkError

        # BaseExceptionGroup from Python 3.11+ has exceptions attribute
        # The exceptiongroup backport also has it
        # But our fallback (Exception) does not
        if hasattr(eg, 'exceptions') and callable(
          getattr(eg, '__iter__', None),
        ):
          exceptions_list = getattr(eg, 'exceptions', [])
          for exc in exceptions_list:
            if isinstance(exc, NetworkError):
              raise exc
        # If no NetworkError found, re-raise the exception group
        raise

      # Wrap each cyclist's data in ZPCyclist object
      results_fetched: dict[int, ZPCyclist] = {}
      for zid in validated_ids:
        if zid in results_fetched_dict:
          results_fetched[zid] = ZPCyclist.from_dict(results_fetched_dict[zid])

      self._raw = results_raw
      self._fetched = results_fetched
      self.processed = {}  # Reserved for future use
      logger.info(
        f'Successfully fetched {len(validated_ids)} cyclist profile(s)',
      )

      return self._fetched

    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  @classmethod
  def set_sync_mode(cls, enabled: bool) -> None:
    """Enable or disable synchronous fetch mode.

    Args:
      enabled: True to enable sync mode, False for async (default)
    """
    cls._sync_mode = enabled
    mode = 'synchronous' if enabled else 'asynchronous (parallel)'
    logger.info(f'Cyclist fetch mode set to: {mode}')

  # ----------------------------------------------------------------------------
  def _fetch_sequential(self, *zwift_id: int) -> dict[int, ZPCyclist]:
    """Fetch cyclist data sequentially (synchronous mode).

    This method provides a clear, separate execution path for debugging.
    All requests are made synchronously in sequence, with no parallelization.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to ZPCyclist objects

    Raises:
      ValueError: If any ID is invalid (non-positive or too large)
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    logger.info(
      f'Fetching cyclist data in synchronous mode for {len(zwift_id)} ID(s)',
    )

    # SECURITY: Validate all Zwift IDs before processing
    try:
      validated_ids = validate_id_list(list(zwift_id), id_type='zwift')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    # Create synchronous ZP session
    zp = ZP()

    results_raw: dict[int, str] = {}
    results_fetched_dict: dict[
      int,
      dict[str, Any],
    ] = {}  # Temporary dict structure

    # Fetch each ID sequentially
    for zid in validated_ids:
      logger.debug(f'Fetching cyclist profile for Zwift ID: {zid}')
      url = f'{self._url}{zid}{self._url_end}'

      # Synchronous blocking call
      raw_json = zp.fetch_json(url)
      results_raw[zid] = raw_json

      # Parse immediately (no parallel parsing)
      parsed = parse_json_safe(raw_json, context=f'cyclist {zid}')
      results_fetched_dict[zid] = parsed if isinstance(parsed, dict) else {}

      logger.debug(f'Successfully fetched profile for Zwift ID: {zid}')

    # Wrap each cyclist's data in ZPCyclist object
    results_fetched: dict[int, ZPCyclist] = {}
    for zid in validated_ids:
      if zid in results_fetched_dict:
        results_fetched[zid] = ZPCyclist.from_dict(results_fetched_dict[zid])

    self._raw = results_raw
    self._fetched = results_fetched
    self.processed = {}  # Reserved for future use

    logger.info(
      f'Successfully fetched {len(validated_ids)} cyclist profile(s) in sync mode',
    )
    return self._fetched

  # ----------------------------------------------------------------------------
  def fetch(self, *zwift_id: int) -> dict[int, ZPCyclist]:
    """Fetch cyclist profile data for one or more Zwift IDs (synchronous).

    Retrieves comprehensive profile data from Zwiftpower cache and profile
    pages. Stores results in the raw dictionary keyed by Zwift ID.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to ZPCyclist objects

    Raises:
      ValueError: If any ID is invalid (non-positive or too large)
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    # Check if sync mode is enabled
    if self._sync_mode:
      return self._fetch_sequential(*zwift_id)

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
      return asyncio.run(self._fetch_parallel(*zwift_id))

  # ----------------------------------------------------------------------------
  async def afetch(self, *zwift_id: int) -> dict[int, ZPCyclist]:
    """Fetch cyclist profile data for one or more Zwift IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Note: Only fetches JSON data, not profile pages.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to ZPCyclist objects

    Raises:
      ValueError: If any ID is invalid (non-positive or too large)
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*zwift_id)

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Return JSON string representation of fetched data.

    Converts ZPCyclist objects to dicts before serialization.

    Returns:
      JSON-formatted string of all fetched cyclist data
    """
    serializable = {
      key: value.asdict() if isinstance(value, ZPCyclist) else value
      for key, value in self._fetched.items()
    }
    return json.JSONEncoder(indent=2).encode(serializable)

  # ----------------------------------------------------------------------------
  def racelog(self, zwift_id: int) -> ZPRacelog:
    """Extract race log from fetched cyclist data as a ZPRacelog object.

    Returns the complete race history for a cyclist wrapped in a ZPRacelog
    object that supports array-like operations. Must call fetch() or
    afetch() before calling this method.

    Args:
      zwift_id: The Zwift ID to get racelog for

    Returns:
      ZPRacelog object containing ZPRaceFinish objects for each race

    Raises:
      ValueError: If no data exists for the given Zwift ID
      KeyError: If the data structure doesn't contain 'data' key

    Example:
      cyclist = Cyclist()
      cyclist.fetch(7574336)
      racelog = cyclist.racelog(7574336)
      print(f"Total races: {len(racelog)}")
      for race in racelog:
        print(f"{race.event_title}: Position {race.pos}")
    """
    if zwift_id not in self._fetched:
      raise ValueError(
        f'No data fetched for Zwift ID {zwift_id}. Call fetch() or afetch() first.',
      )

    cyclist_obj = self._fetched[zwift_id]
    # ZPCyclist has a racelog property that returns ZPRacelog
    return cyclist_obj.racelog


# ==============================================================================
def main() -> None:
  desc = """
Module for fetching cyclist data using the Zwiftpower API
  """
  p = ArgumentParser(description=desc)
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
    help='raw results',
  )
  p.add_argument('zwift_id', type=int, nargs='+', help='a list of zwift_ids')
  args = p.parse_args()

  # Configure logging based on verbosity level (output to stderr)
  if args.verbose >= 2:
    setup_logging(console_level='DEBUG', force_console=True)
  elif args.verbose == 1:
    setup_logging(console_level='INFO', force_console=True)

  x = ZPCyclistFetch()

  x.fetch(*args.zwift_id)

  if args.raw:
    print(x.raw)


# ==============================================================================
if __name__ == '__main__':
  main()
