"""Unified Primes class with both sync and async fetch capabilities."""

import asyncio
import datetime
import re
from argparse import ArgumentParser
from collections.abc import Coroutine
from typing import Any

import anyio

from shared.validation import ValidationError, validate_id_list
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger, setup_logging
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Primes(ZP_obj):
  """Fetches and stores race prime (sprint/KOM) data from Zwiftpower.

  Retrieves prime segment results for races, including both fastest
  absolute lap (FAL/msec) and first to sprint (FTS/elapsed) primes
  across all categories. Supports both synchronous and asynchronous operations.

  Synchronous usage:
    primes = Primes()
    primes.fetch(3590800, 3590801)
    print(primes.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      primes = Primes()
      primes.set_session(zp)
      await primes.afetch(3590800, 3590801)
      print(primes.json())

  Attributes:
    raw: Nested dictionary mapping race IDs -> categories -> prime types to data
    verbose: Enable verbose output for debugging
  """

  # https://zwiftpower.com/api3.php?do=event_primes&zid={race_id}&category={cat}&prime_type={type}
  _url_base: str = 'https://zwiftpower.com/api3.php?do=event_primes'
  _url_race_id: str = '&zid='
  _url_category: str = '&category='
  _url_primetype: str = '&prime_type='
  _cat: list[str] = ['A', 'B', 'C', 'D', 'E']
  _type: list[str] = ['msec', 'elapsed']

  # Async version uses different URLs
  _url_async: str = 'https://zwiftpower.com/cache3/primes/'
  _url_end_async: str = '.json'

  def __init__(self) -> None:
    """Initialize a new Primes instance."""
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
    """Set the ZP session to use for sync fetching.

    The cookies from this session will be shared with an async client
    for parallel requests, but the sync session itself is not used
    for fetching.

    Args:
      zp: ZP instance to use for API requests (shared across objects)
    """
    self._zp_sync = zp

  # -------------------------------------------------------------------------------
  @classmethod
  def set_primetype(cls, t: str) -> str:
    """Convert prime type string to Zwiftpower API code or descriptive string.

    Args:
      t: Prime type string ('msec', 'elapsed', 'sprint', 'kom', 'prime')

    Returns:
      API code ('FAL' for fastest absolute lap, 'FTS' for first to sprint,
      or descriptive string like 'Sprint', 'KOM', 'Prime', or empty string for unknown)
    """
    match t.lower():
      case 'msec':
        return 'FAL'
      case 'elapsed':
        return 'FTS'
      case 'sprint':
        return 'Sprint'
      case 'kom':
        return 'KOM'
      case 'prime':
        return 'Prime'
      case _:
        return ''

  # -------------------------------------------------------------------------------
  async def _get_or_create_session(self) -> tuple[AsyncZP, bool]:
    """Get existing session or create temporary one.

    Returns:
      Tuple of (AsyncZP session, owns_session bool)
      - If owns_session is True, caller must close the session
      - If owns_session is False, session is shared and must not be closed
    """
    # Case 1: Already have async session (set via set_session)
    if self._zp:
      logger.debug('Using existing AsyncZP session')
      return (self._zp, False)

    # Case 2: Have sync session (set via set_zp_session) - convert to async
    if self._zp_sync:
      logger.debug('Creating AsyncZP wrapper for shared sync session')
      # Create async client that shares cookies with sync session
      async_zp = AsyncZP(skip_credential_check=True)
      await async_zp.init_client()

      # Copy authentication state from sync to async client
      if self._zp_sync._client and async_zp._client:
        # Share the cookies - this preserves the login session
        async_zp._client.cookies = self._zp_sync._client.cookies
        logger.debug('Copied authentication cookies from sync to async session')

      # Don't store this - create fresh each time to avoid lifecycle issues
      return (async_zp, True)  # We own this temporary wrapper

    # Case 3: No session - create temporary one
    logger.debug('Creating temporary AsyncZP session')
    temp_zp = AsyncZP(skip_credential_check=True)
    await temp_zp.login()
    return (temp_zp, True)

  # -------------------------------------------------------------------------------
  async def _fetch_parallel(self, *race_id: int) -> dict[Any, Any]:
    """Internal method that performs parallel fetching (always async).

    This is the core implementation used by both fetch() and afetch().
    Handles both shared sessions and temporary sessions.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Nested dictionary: {race_id: {category: {prime_type: data}}}

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    # Get session (shared or temporary)
    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching prime data for {len(race_id)} race(s)')

      # SECURITY: Validate all race IDs before processing
      try:
        validated_ids = validate_id_list(list(race_id), id_type='race')
        logger.debug(f'Validated {len(validated_ids)} race IDs')
      except ValidationError as e:
        logger.error(f'ID validation failed: {e}')
        raise

      p: dict[Any, Any] = {}
      ts = int(re.sub(r'\.', '', str(datetime.datetime.now().timestamp())[:-3]))

      # Build all URLs and prepare structure
      fetch_tasks = []
      url_mapping = []  # Track (race, cat, primetype) for each URL

      for race in validated_ids:
        p[race] = {}
        for cat in self._cat:
          p[race][cat] = {}
          for primetype in self._type:
            url = f'{self._url_base}{self._url_race_id}{race}{self._url_category}{cat}{self._url_primetype}{primetype}&_={ts}'
            fetch_tasks.append(session.fetch_json(url))
            url_mapping.append((race, cat, primetype))
            ts += 1

      # Fetch all URLs in parallel using anyio for cross-backend compatibility
      logger.info(f'Sending {len(fetch_tasks)} requests in parallel')
      results = [None] * len(fetch_tasks)

      async def fetch_and_store(
        idx: int,
        task: Coroutine[Any, Any, dict[str, Any]],
      ) -> None:
        """Fetch a single URL and store the result."""
        try:
          results[idx] = await task
        except Exception as e:
          results[idx] = e

      async with anyio.create_task_group() as tg:
        for idx, task in enumerate(fetch_tasks):
          tg.start_soon(fetch_and_store, idx, task)

      # Process results
      for idx, result in enumerate(results):
        race, cat, primetype = url_mapping[idx]

        if isinstance(result, Exception):
          logger.error(
            f'Error fetching {primetype} for race {race} cat {cat}: {result}',
          )
          p[race][cat][primetype] = {'data': [], 'error': str(result)}
        else:
          if 'data' not in result or len(result['data']) == 0:
            logger.debug(f'No results for {primetype} in category {cat}')
          else:
            logger.debug(f'Results found for {primetype} in category {cat}')
          p[race][cat][primetype] = result

      self.raw = p
      logger.info(f'Successfully fetched prime data for {len(validated_ids)} race(s)')
      self.processed = self.raw
      return self.processed

    finally:
      # Only close if we created a temporary session
      if owns_session:
        await session.close()

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch prime data for one or more race IDs (synchronous).

    Retrieves prime results for all categories (A-E) and both prime types
    (msec/FAL and elapsed/FTS) for each race.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Nested dictionary: {race_id: {category: {prime_type: data}}}

    Raises:
      ValueError: If any race ID is invalid
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
      return asyncio.run(self._fetch_parallel(*race_id))

  # -------------------------------------------------------------------------------
  async def afetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch prime data for one or more race IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Nested dictionary: {race_id: {category: {prime_type: data}}}

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*race_id)


# ===============================================================================
def main() -> None:
  desc = """
Module for fetching primes using the Zwiftpower API
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
    help='print all returned data',
  )
  p.add_argument('race_id', type=int, nargs='+', help='one or more race_ids')
  args = p.parse_args()

  # Configure logging based on verbosity level (output to stderr)
  if args.verbose >= 2:
    setup_logging(console_level='DEBUG', force_console=True)
  elif args.verbose == 1:
    setup_logging(console_level='INFO', force_console=True)

  x = Primes()

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
