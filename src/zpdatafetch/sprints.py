"""Unified Sprints class with both sync and async fetch capabilities."""

import asyncio
from argparse import ArgumentParser
from typing import Any

import anyio

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger, setup_logging
from zpdatafetch.primes import Primes
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj

logger = get_logger(__name__)


# ===============================================================================
class Sprints(ZP_obj):
  """Fetches and stores race sprint data from Zwiftpower.

  Retrieves sprint segment results for races using the event_sprints API.
  Supports both synchronous and asynchronous operations.

  Synchronous usage:
    sprints = Sprints()
    sprints.fetch(3590800, 3590801)
    print(sprints.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      sprints = Sprints()
      sprints.set_session(zp)
      await sprints.afetch(3590800, 3590801)
      print(sprints.json())

  Attributes:
    raw: Dictionary mapping race IDs to their sprint data
    verbose: Enable verbose output for debugging
  """

  # https://zwiftpower.com/api3.php?do=event_sprints&zid=<race_id>
  _url: str = 'https://zwiftpower.com/api3.php?do=event_sprints&zid='

  def __init__(self) -> None:
    """Initialize a new Sprints instance."""
    super().__init__()
    self._zp: AsyncZP | None = None  # Async session
    self._zp_sync: ZP | None = None  # Sync session (for reference only)
    self.primes: Primes = Primes()
    self.banners: list[dict[str, Any]] = []
    self.processed: dict[Any, Any] = {}

  # -------------------------------------------------------------------------------
  def set_session(self, zp: AsyncZP) -> None:
    """Set the AsyncZP session to use for async fetching.

    Args:
      zp: AsyncZP instance to use for API requests
    """
    self._zp = zp
    self.primes.set_session(zp)

  # -------------------------------------------------------------------------------
  def set_zp_session(self, zp: ZP) -> None:
    """Set the ZP session to use for fetching.

    Cookies from this session will be shared with async client.

    Args:
      zp: ZP instance to use for API requests
    """
    self._zp_sync = zp
    self.primes.set_zp_session(zp)

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
  async def _fetch_parallel(self, *race_id: int) -> dict[Any, Any]:
    """Fetch sprint data in parallel using async requests.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their sprint data
    """
    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching sprint data for {len(race_id)} race(s)')

      # SECURITY: Validate all race IDs before processing
      validated_ids = []
      for r in race_id:
        try:
          # Convert to int if string, validate range
          rid = int(r) if not isinstance(r, int) else r
          if rid <= 0 or rid > 999999999:
            raise ValueError(
              f'Invalid race ID: {r}. Must be a positive integer.',
            )
          validated_ids.append(rid)
        except (ValueError, TypeError) as e:
          if isinstance(e, ValueError) and 'Invalid race ID' in str(e):
            raise
          raise ValueError(
            f'Invalid race ID: {r}. Must be a valid positive integer.',
          ) from e

      # Build list of fetch tasks
      fetch_tasks = []
      for rid in validated_ids:
        url = f'{self._url}{rid}'
        fetch_tasks.append(session.fetch_json(url))

      # Execute all fetches in parallel
      results = {}

      async def fetch_and_store(idx: int, task: Any) -> None:
        """Helper to fetch and store result."""
        try:
          result = await task
          results[validated_ids[idx]] = result
          logger.debug(
            f'Successfully fetched sprints for race ID: {validated_ids[idx]}',
          )
        except Exception as e:
          logger.error(f'Failed to fetch race ID {validated_ids[idx]}: {e}')
          raise

      async with anyio.create_task_group() as tg:
        for idx, task in enumerate(fetch_tasks):
          tg.start_soon(fetch_and_store, idx, task)

      self.raw = results
      logger.info(f'Successfully fetched {len(validated_ids)} race sprint(s)')

      # Share the session with primes to avoid second login
      self.primes.set_session(session)
      await self.primes.afetch(*validated_ids)
      self.extract_banners()
      self.enrich_sprints()

      return self.processed

    finally:
      if owns_session:
        await session.close()

  # -------------------------------------------------------------------------------
  def extract_banners(self) -> list[dict[str, Any]]:
    """Extract sprint_id and name from primes data to build banner list.

    Loops through the primes data and extracts sprint_id and name fields
    to create a list of banner dictionaries.

    Returns:
      List of dictionaries with sprint_id and name keys

    Example:
      [
        {"sprint_id": 133, "name": "Manhattan Sprint Reverse"},
        {"sprint_id": 132, "name": "Manhattan Sprint"},
        {"sprint_id": 32, "name": "NY Sprint 2"}
      ]
    """
    logger.debug('Extracting banners from primes data')
    banners: list[dict[str, Any]] = []

    # Loop through primes data structure: race_id -> category -> prime_type -> data
    for race_id, categories in self.primes.raw.items():
      logger.debug(f'Processing race ID: {race_id}')
      for category, prime_types in categories.items():
        for prime_type, prime_data in prime_types.items():
          # Check if 'data' key exists and has items
          if prime_data.get('data'):
            for item in prime_data['data']:
              # Extract sprint_id and name if they exist
              if 'sprint_id' in item and 'name' in item:
                banner = {
                  'sprint_id': item['sprint_id'],
                  'name': item['name'],
                }
                # Avoid duplicates
                if banner not in banners:
                  banners.append(banner)
                  logger.debug(f'Added banner: {banner}')

    self.banners = banners
    logger.info(f'Extracted {len(banners)} unique banner(s)')
    logger.debug(f'{banners}')
    return self.banners

  # -------------------------------------------------------------------------------
  def enrich_sprints(self) -> dict[Any, Any]:
    """Enrich sprint data by replacing sprint IDs with banner names.

    Creates a deep copy of self.raw and replaces sprint_id keys (like "32", "132")
    with their corresponding banner names from self.banners in sections like
    "msec", "watts", and "wkg".

    Returns:
      Dictionary with enriched sprint data stored in self.processed
    """
    import copy

    logger.debug('Enriching sprint data with banner names')

    # Create sprint_id to name mapping for quick lookup
    id_to_name: dict[str, str] = {}
    for banner in self.banners:
      sprint_id = str(banner['sprint_id'])
      name = banner['name']
      id_to_name[sprint_id] = name
      logger.debug(f'Mapping sprint_id {sprint_id} -> {name}')

    # Deep copy raw data to processed
    self.processed = copy.deepcopy(self.raw)

    # Loop through the processed data structure
    for race_id, race_data in self.processed.items():
      logger.debug(f'Processing race ID: {race_id}')

      # race_data should be a dict or list of dicts
      if isinstance(race_data, dict):
        # Look for data arrays containing sprint results
        if 'data' in race_data and isinstance(race_data['data'], list):
          for rider in race_data['data']:
            if isinstance(rider, dict):
              # Replace sprint IDs in msec, watts, wkg sections
              for section in ['msec', 'watts', 'wkg']:
                if section in rider and isinstance(rider[section], dict):
                  # Create new dict with banner names as keys
                  enriched_section = {}
                  for sprint_id, value in rider[section].items():
                    banner_name = id_to_name.get(sprint_id, sprint_id)
                    enriched_section[banner_name] = value
                    if banner_name != sprint_id:
                      logger.debug(
                        f'Replaced {sprint_id} with {banner_name} in {section}',
                      )
                  rider[section] = enriched_section

    logger.info(f'Enriched sprint data for {len(self.processed)} race(s)')
    return self.processed

  # -------------------------------------------------------------------------------
  def fetch(self, *race_id: int) -> dict[Any, Any]:
    """Fetch sprint data for one or more race IDs (synchronous).

    Retrieves sprint segment results for each race ID.
    Stores results in the raw dictionary keyed by race ID.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their sprint data

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
    """Fetch sprint data for one or more race IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their sprint data

    Raises:
      ValueError: If any race ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*race_id)


# ===============================================================================
def main() -> None:
  desc = """
Module for fetching sprints using the Zwiftpower API
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

  x = Sprints()

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ===============================================================================
if __name__ == '__main__':
  main()
