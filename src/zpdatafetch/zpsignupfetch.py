"""Unified Signup class with both sync and async fetch capabilities."""

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
from zpdatafetch.zpracesignup import ZPRaceSignup

logger = get_logger(__name__)


# ==============================================================================
class ZPSignupFetch(ZP_obj):
  """Fetches and stores race signup data from Zwiftpower.

  Retrieves lists of riders who have signed up for races, including
  their registration details and categories. Supports both synchronous
  and asynchronous operations.

  Synchronous usage:
    signup = ZPSignupFetch()
    signup.fetch(3590800, 3590801)
    print(signup.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      signup = ZPSignupFetch()
      signup.set_session(zp)
      await signup.afetch(3590800, 3590801)
      print(signup.json())

  Attributes:
    raw: Dictionary mapping race IDs to ZPRaceSignup objects
    verbose: Enable verbose output for debugging
  """

  # Both sync and async use the same endpoint
  _url: str = 'https://zwiftpower.com/cache3/results/'
  _url_end: str = '_signups.json'
  _sync_mode: bool = False  # Class-level sync mode flag

  def __init__(self) -> None:
    """Initialize a new Signup instance."""
    super().__init__()
    self._fetched: dict[
      int,
      ZPRaceSignup,
    ] = {}  # Override type to use ZPRaceSignup
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
  async def _fetch_parallel(
    self,
    *race_id_list: int,
  ) -> dict[int, ZPRaceSignup]:
    """Fetch race signups in parallel using async requests.

    Args:
      *race_id_list: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to ZPRaceSignup objects
    """
    # SECURITY: Validate all race IDs before creating session
    # This avoids expensive login/session creation for invalid IDs
    try:
      validated_ids = validate_id_list(list(race_id_list), id_type='race')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching race signups for {len(race_id_list)} race(s)')

      # Build list of fetch tasks using correct URL
      fetch_tasks = []
      for rid in validated_ids:
        url = f'{self._url}{rid}{self._url_end}'
        fetch_tasks.append(session.fetch_json(url))

      # Execute all fetches in parallel

      results_raw: dict[int, str] = {}

      results_fetched: dict[int, ZPRaceSignup] = {}

      async def fetch_and_store(
        idx: int,
        task: Coroutine[Any, Any, str],
      ) -> None:
        """Helper to fetch and store result."""
        try:
          raw_json = await task
          event_id = validated_ids[idx]
          results_raw[event_id] = raw_json

          # Parse for fetched dict and wrap in ZPRaceSignup
          parsed = parse_json_safe(raw_json, context=f'signup {event_id}')
          signup_dict = parsed if isinstance(parsed, dict) else {}
          results_fetched[event_id] = ZPRaceSignup.from_dict(signup_dict)

          logger.debug(
            f'Successfully fetched event ID: {event_id}',
          )
        except Exception as e:
          logger.error(f'Failed to fetch race ID {validated_ids[idx]}: {e}')
          raise

      async with anyio.create_task_group() as tg:
        for idx, task in enumerate(fetch_tasks):
          tg.start_soon(fetch_and_store, idx, task)

      self._raw = results_raw
      self._fetched = results_fetched
      self.processed = {}  # Reserved for future use
      logger.info(
        f'Successfully fetched {len(validated_ids)} race signup list(s)',
      )

      return self._fetched

    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  def _fetch_sequential(self, *race_id: int) -> dict[int, ZPRaceSignup]:
    """Fetch signup data sequentially (synchronous mode).

    This method provides a clear, separate execution path for debugging.
    All requests are made synchronously in sequence, with no parallelization.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their data

    Raises:
      ValueError: If any ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    logger.info(
      f'Fetching signup data in synchronous mode for {len(race_id)} ID(s)',
    )

    # SECURITY: Validate all IDs before processing
    try:
      validated_ids = validate_id_list(list(race_id), id_type='race')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    # Create synchronous ZP session
    zp = ZP()

    results_raw: dict[int, str] = {}
    results_fetched: dict[int, ZPRaceSignup] = {}

    # Fetch each ID sequentially
    for id_val in validated_ids:
      logger.debug(f'Fetching signup data for race ID: {id_val}')
      url = f'{self._url}{id_val}{self._url_end}'

      # Synchronous blocking call
      raw_json = zp.fetch_json(url)
      results_raw[id_val] = raw_json

      # Parse immediately (no parallel parsing) and wrap in ZPRaceSignup
      parsed = parse_json_safe(raw_json, context=f'signup {id_val}')
      signup_dict = parsed if isinstance(parsed, dict) else {}
      results_fetched[id_val] = ZPRaceSignup.from_dict(signup_dict)

      logger.debug(f'Successfully fetched signup data for race ID: {id_val}')

    self._raw = results_raw

    self._fetched = results_fetched

    self.processed = {}  # Reserved for future use

    logger.info(
      f'Successfully fetched {len(validated_ids)} signup(s) in sync mode',
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
    logger.info(f'Signup fetch mode set to: {mode}')

  def json(self) -> str:
    """Serialize the fetched data to formatted JSON string.

    Converts ZPRaceSignup objects to dicts before serialization.

    Returns:
      JSON string with 2-space indentation
    """
    # Convert ZPRaceSignup objects to dicts
    serializable = {
      key: value.asdict() if isinstance(value, ZPRaceSignup) else value
      for key, value in self._fetched.items()
    }
    return json.JSONEncoder(indent=2).encode(serializable)

  # ----------------------------------------------------------------------------
  def fetch(self, *race_id_list: int) -> dict[int, ZPRaceSignup]:
    """Fetch race signup data for one or more race IDs (synchronous).

    Retrieves the list of signed-up participants from Zwiftpower cache.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id_list: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to ZPRaceSignup objects

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    # Check if sync mode is enabled
    if self._sync_mode:
      return self._fetch_sequential(*race_id_list)

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
      return asyncio.run(self._fetch_parallel(*race_id_list))

  # ----------------------------------------------------------------------------
  async def afetch(self, *race_id: int) -> dict[int, ZPRaceSignup]:
    """Fetch signup lists for one or more race IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to ZPRaceSignup objects

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*race_id)


# ==============================================================================
def main() -> None:
  p = ArgumentParser(
    description='Module for fetching race signup data using the Zwiftpower API',
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
  p.add_argument('race_id', type=int, nargs='+', help='one or more race_ids')
  args = p.parse_args()

  # Configure logging based on verbosity level (output to stderr)
  if args.verbose >= 2:
    setup_logging(console_level='DEBUG', force_console=True)
  elif args.verbose == 1:
    setup_logging(console_level='INFO', force_console=True)

  x = ZPSignupFetch()

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ==============================================================================
if __name__ == '__main__':
  main()
