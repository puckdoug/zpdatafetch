"""Unified Primes class with both sync and async fetch capabilities."""

import asyncio
import datetime
import json
import re
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
from zpdatafetch.zpprime import ZPPrime

logger = get_logger(__name__)


# ==============================================================================
class ZPPrimesFetch(ZP_obj):
  """Fetches and stores race prime (sprint/KOM) data from Zwiftpower.

  Retrieves prime segment results for races, including both fastest
  absolute lap (FAL/msec) and first to sprint (FTS/elapsed) primes
  across all categories. Supports both synchronous and asynchronous operations.

  Synchronous usage:
    primes = ZPPrimesFetch()
    primes.fetch(3590800, 3590801)
    print(primes.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      primes = ZPPrimesFetch()
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
  _sync_mode: bool = False  # Class-level sync mode flag

  def __init__(self) -> None:
    """Initialize a new Primes instance."""
    super().__init__()
    self._fetched: dict[int, ZPPrime] = {}  # Override type
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
    """Set the ZP session to use for sync fetching.

    The cookies from this session will be shared with an async client
    for parallel requests, but the sync session itself is not used
    for fetching.

    Args:
      zp: ZP instance to use for API requests (shared across objects)
    """
    self._zp_sync = zp

  # ----------------------------------------------------------------------------
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

  # ----------------------------------------------------------------------------
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
        assert async_zp._client is not None
      assert self._zp_sync._client is not None
      async_zp._client.cookies = self._zp_sync._client.cookies  # type: ignore[assignment]
      logger.debug('Copied authentication cookies from sync to async session')

      # Don't store this - create fresh each time to avoid lifecycle issues
      return (async_zp, True)  # We own this temporary wrapper

    # Case 3: No session - create temporary one
    logger.debug('Creating temporary AsyncZP session')
    temp_zp = AsyncZP(skip_credential_check=True)
    await temp_zp.login()
    return (temp_zp, True)

  # ----------------------------------------------------------------------------
  async def _fetch_parallel(self, *race_id: int) -> dict[int, ZPPrime]:
    """Internal method that performs parallel fetching (always async).

    This is the core implementation used by both fetch() and afetch().
    Handles both shared sessions and temporary sessions.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to ZPPrime objects

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    # SECURITY: Validate all race IDs before creating session
    # This avoids expensive login/session creation for invalid IDs
    try:
      validated_ids = validate_id_list(list(race_id), id_type='race')
      logger.debug(f'Validated {len(validated_ids)} race IDs')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    # Get session (shared or temporary)
    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching prime data for {len(race_id)} race(s)')

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
      results_raw = [None] * len(fetch_tasks)
      results_parsed = [None] * len(fetch_tasks)

      async def fetch_and_store(
        idx: int,
        task: Coroutine[Any, Any, str],
      ) -> None:
        """Fetch a single URL and store the result."""
        try:
          raw_json = await task
          results_raw[idx] = raw_json
          # Parse JSON for processing
          race, cat, primetype = url_mapping[idx]
          parsed = parse_json_safe(
            raw_json,
            context=f'prime {race}/{cat}/{primetype}',
          )
          results_parsed[idx] = parsed if isinstance(parsed, dict) else {}
        except Exception as e:
          results_raw[idx] = e
          results_parsed[idx] = e

      async with anyio.create_task_group() as tg:
        for idx, task in enumerate(fetch_tasks):
          tg.start_soon(fetch_and_store, idx, task)

      # Build nested structures for raw (strings) and fetched (dicts)
      p_raw: dict[Any, Any] = {}
      p_fetched_dict: dict[Any, Any] = {}  # Temporary dict structure

      for race in validated_ids:
        p_raw[race] = {}
        p_fetched_dict[race] = {}
        for cat in self._cat:
          p_raw[race][cat] = {}
          p_fetched_dict[race][cat] = {}

      # Organize results into nested structure
      for idx, (raw_result, parsed_result) in enumerate(
        zip(results_raw, results_parsed, strict=False),
      ):
        race, cat, primetype = url_mapping[idx]

        if isinstance(raw_result, Exception):
          logger.error(
            f'Error fetching {primetype} for race {race} cat {cat}: {raw_result}',
          )
          error_json = json.dumps({'data': [], 'error': str(raw_result)})
          p_raw[race][cat][primetype] = error_json
          p_fetched_dict[race][cat][primetype] = {
            'data': [],
            'error': str(raw_result),
          }
        else:
          p_raw[race][cat][primetype] = raw_result
          p_fetched_dict[race][cat][primetype] = parsed_result

          if 'data' not in parsed_result or len(parsed_result.get('data', [])) == 0:
            logger.debug(f'No results for {primetype} in category {cat}')
          else:
            logger.debug(f'Results found for {primetype} in category {cat}')

      # Wrap each race's data in ZPPrime object
      p_fetched: dict[int, ZPPrime] = {}
      for race in validated_ids:
        prime_obj = ZPPrime(p_fetched_dict[race])
        prime_obj.race_id = race  # Inject race_id
        p_fetched[race] = prime_obj

      self._raw = p_raw
      self._fetched = p_fetched
      self.processed = {}  # Reserved for future use
      logger.info(
        f'Successfully fetched prime data for {len(validated_ids)} race(s)',
      )
      return self._fetched

    finally:
      # Only close if we created a temporary session
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  def _fetch_sequential(self, *race_id: int) -> dict[int, ZPPrime]:
    """Fetch primes data sequentially (synchronous mode).

    This method provides a clear, separate execution path for debugging.
    All requests are made synchronously in sequence, with no parallelization.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to ZPPrime objects

    Raises:
      ValueError: If any ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    logger.info(
      f'Fetching primes data in synchronous mode for {len(race_id)} race(s)',
    )

    # SECURITY: Validate all IDs before processing
    try:
      validated_ids = validate_id_list(list(race_id), id_type='race')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    # Create synchronous ZP session
    zp = ZP()

    # Initialize nested structures
    p_raw: dict[Any, Any] = {}
    p_fetched_dict: dict[Any, Any] = {}  # Temporary dict structure
    ts = int(re.sub(r'\.', '', str(datetime.datetime.now().timestamp())[:-3]))

    # Fetch each race sequentially
    for race in validated_ids:
      logger.debug(f'Fetching primes data for race ID: {race}')
      p_raw[race] = {}
      p_fetched_dict[race] = {}

      # Fetch each category sequentially
      for cat in self._cat:
        p_raw[race][cat] = {}
        p_fetched_dict[race][cat] = {}

        # Fetch each prime type sequentially
        for primetype in self._type:
          url = f'{self._url_base}{self._url_race_id}{race}{self._url_category}{cat}{self._url_primetype}{primetype}&_={ts}'

          # Synchronous blocking call
          try:
            raw_json = zp.fetch_json(url)
            p_raw[race][cat][primetype] = raw_json

            # Parse immediately
            parsed = parse_json_safe(
              raw_json,
              context=f'prime {race}/{cat}/{primetype}',
            )
            p_fetched_dict[race][cat][primetype] = (
              parsed if isinstance(parsed, dict) else {}
            )

            if 'data' not in parsed or (
              isinstance(parsed, dict) and len(parsed.get('data', [])) == 0
            ):
              logger.debug(f'No results for {primetype} in category {cat}')
            else:
              logger.debug(f'Results found for {primetype} in category {cat}')
          except Exception as e:
            logger.error(
              f'Error fetching {primetype} for race {race} cat {cat}: {e}',
            )
            error_json = json.dumps({'data': [], 'error': str(e)})
            p_raw[race][cat][primetype] = error_json
            p_fetched_dict[race][cat][primetype] = {'data': [], 'error': str(e)}

          ts += 1

    # Wrap each race's data in ZPPrime object
    p_fetched: dict[int, ZPPrime] = {}
    for race in validated_ids:
      prime_obj = ZPPrime(p_fetched_dict[race])
      prime_obj.race_id = race  # Inject race_id
      p_fetched[race] = prime_obj

    self._raw = p_raw
    self._fetched = p_fetched
    self.processed = {}  # Reserved for future use

    logger.info(
      f'Successfully fetched {len(validated_ids)} race(s) in sync mode',
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
    logger.info(f'Primes fetch mode set to: {mode}')

  def fetch(self, *race_id: int) -> dict[int, ZPPrime]:
    """Fetch prime data for one or more race IDs (synchronous).

    Retrieves prime results for all categories (A-E) and both prime types
    (msec/FAL and elapsed/FTS) for each race.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to ZPPrime objects

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    # Check if sync mode is enabled
    if self._sync_mode:
      return self._fetch_sequential(*race_id)

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
      return asyncio.run(self._fetch_parallel(*race_id))

  # ----------------------------------------------------------------------------
  async def afetch(self, *race_id: int) -> dict[int, ZPPrime]:
    """Fetch prime data for one or more race IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to ZPPrime objects

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*race_id)

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Return JSON string representation of fetched data.

    Converts ZPPrime objects to dicts before serialization.

    Returns:
      JSON-formatted string of all fetched prime data
    """
    serializable = {
      key: value.asdict() if isinstance(value, ZPPrime) else value
      for key, value in self._fetched.items()
    }
    return json.JSONEncoder(indent=2).encode(serializable)


# ==============================================================================
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

  x = ZPPrimesFetch()

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ==============================================================================
if __name__ == '__main__':
  main()
