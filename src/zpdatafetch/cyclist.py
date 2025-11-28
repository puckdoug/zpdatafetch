"""Unified Cyclist class with both sync and async fetch capabilities."""

import asyncio
from argparse import ArgumentParser
from typing import Any

import anyio

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger, setup_logging
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Cyclist(ZP_obj):
  """Fetches and stores cyclist profile data from Zwiftpower.

  Retrieves cyclist information including performance metrics, race history,
  and profile details using Zwift IDs. Supports both synchronous and
  asynchronous operations.

  Synchronous usage:
    cyclist = Cyclist()
    cyclist.fetch(123456, 789012)
    print(cyclist.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      cyclist = Cyclist()
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

  def __init__(self) -> None:
    """Initialize a new Cyclist instance."""
    super().__init__()
    self._zp: AsyncZP | None = None  # Async session
    self._zp_sync: ZP | None = None  # Sync session (for reference only)
    self.processed: dict[Any, Any] = {}

  # -------------------------------------------------------------------------------
  def set_session(self, zp: AsyncZP) -> None:
    """Set the AsyncZP session to use for async fetching.

    Args:
      zp: AsyncZP instance to use for API requests
    """
    self._zp = zp

  # -------------------------------------------------------------------------------
  def set_zp_session(self, zp: ZP) -> None:
    """Set the ZP session to use for fetching.

    Cookies from this session will be shared with async client.

    Args:
      zp: ZP instance to use for API requests
    """
    self._zp_sync = zp

  # -------------------------------------------------------------------------------
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
      async_zp._client.cookies = self._zp_sync._client.cookies
      return (async_zp, True)

    # Case 3: Create temporary session with login
    temp_zp = AsyncZP(skip_credential_check=True)
    await temp_zp.login()
    return (temp_zp, True)

  # -------------------------------------------------------------------------------
  async def _fetch_parallel(self, *zwift_id: int) -> dict[Any, Any]:
    """Fetch cyclist data in parallel using async requests.

    Note: Only fetches JSON data, not profile pages.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to their profile data
    """
    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching cyclist data for {len(zwift_id)} ID(s)')

      # SECURITY: Validate all Zwift IDs before processing
      validated_ids = []
      for z in zwift_id:
        try:
          # Convert to int if string, validate range
          zid = int(z) if not isinstance(z, int) else z
          if zid <= 0 or zid > 999999999:
            raise ValueError(
              f'Invalid Zwift ID: {z}. Must be a positive integer.',
            )
          validated_ids.append(zid)
        except (ValueError, TypeError) as e:
          if isinstance(e, ValueError) and 'Invalid Zwift ID' in str(e):
            raise
          raise ValueError(
            f'Invalid Zwift ID: {z}. Must be a valid positive integer.',
          ) from e

      # Build list of fetch tasks (JSON only, not profile pages)
      fetch_tasks = []
      for zid in validated_ids:
        url = f'{self._url}{zid}{self._url_end}'
        fetch_tasks.append(session.fetch_json(url))

      # Execute all fetches in parallel
      results = {}

      async def fetch_and_store(idx: int, task: Any) -> None:
        """Helper to fetch and store result."""
        try:
          result = await task
          results[validated_ids[idx]] = result
          logger.debug(
            f'Successfully fetched profile for Zwift ID: {validated_ids[idx]}',
          )
        except Exception as e:
          logger.error(f'Failed to fetch Zwift ID {validated_ids[idx]}: {e}')
          raise

      async with anyio.create_task_group() as tg:
        for idx, task in enumerate(fetch_tasks):
          tg.start_soon(fetch_and_store, idx, task)

      self.raw = results
      logger.info(f'Successfully fetched {len(validated_ids)} cyclist profile(s)')

      self.processed = self.raw
      return self.processed

    finally:
      if owns_session:
        await session.close()

  # -------------------------------------------------------------------------------
  def fetch(self, *zwift_id: int) -> dict[Any, Any]:
    """Fetch cyclist profile data for one or more Zwift IDs (synchronous).

    Retrieves comprehensive profile data from Zwiftpower cache and profile
    pages. Stores results in the raw dictionary keyed by Zwift ID.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to their profile data

    Raises:
      ValueError: If any ID is invalid (non-positive or too large)
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
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

  # -------------------------------------------------------------------------------
  async def afetch(self, *zwift_id: int) -> dict[Any, Any]:
    """Fetch cyclist profile data for one or more Zwift IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Note: Only fetches JSON data, not profile pages.

    Args:
      *zwift_id: One or more Zwift ID integers to fetch

    Returns:
      Dictionary mapping Zwift IDs to their profile data

    Raises:
      ValueError: If any ID is invalid (non-positive or too large)
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*zwift_id)


# ===============================================================================
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

  x = Cyclist()

  x.fetch(*args.zwift_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
