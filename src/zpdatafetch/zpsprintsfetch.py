"""Unified Sprints class with both sync and async fetch capabilities."""

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
from zpdatafetch.zpprimesfetch import ZPPrimesFetch
from zpdatafetch.zpracesprint import ZPRaceSprint, ZPRiderSprint

logger = get_logger(__name__)


# ==============================================================================
class ZPSprintsFetch(ZP_obj):
  """Fetches and stores race sprint data from Zwiftpower.

  Retrieves sprint segment results for races using the event_sprints API.
  Supports both synchronous and asynchronous operations.

  Synchronous usage:
    sprints = ZPSprintsFetch()
    sprints.fetch(3590800, 3590801)
    print(sprints.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      sprints = ZPSprintsFetch()
      sprints.set_session(zp)
      await sprints.afetch(3590800, 3590801)
      print(sprints.json())

  Attributes:
    raw: Dictionary mapping race IDs to their sprint data
    verbose: Enable verbose output for debugging
  """

  # https://zwiftpower.com/api3.php?do=event_sprints&zid=<race_id>
  _url: str = 'https://zwiftpower.com/api3.php?do=event_sprints&zid='
  _sync_mode: bool = False  # Class-level sync mode flag

  def __init__(self) -> None:
    """Initialize a new Sprints instance."""
    super().__init__()
    self._fetched: dict[int, ZPRaceSprint] = {}  # Override type
    self._zp: AsyncZP | None = None  # Async session
    self._zp_sync: ZP | None = None  # Sync session (for reference only)
    self.primes: ZPPrimesFetch = ZPPrimesFetch()
    self.banners: list[dict[str, Any]] = []
    self.processed: dict[Any, Any] = {}

  # ----------------------------------------------------------------------------
  def set_session(self, zp: AsyncZP) -> None:
    """Set the AsyncZP session to use for async fetching.

    Args:
      zp: AsyncZP instance to use for API requests
    """
    self._zp = zp
    self.primes.set_session(zp)

  # ----------------------------------------------------------------------------
  def set_zp_session(self, zp: ZP) -> None:
    """Set the ZP session to use for fetching.

    Cookies from this session will be shared with async client.

    Args:
      zp: ZP instance to use for API requests
    """
    self._zp_sync = zp
    self.primes.set_zp_session(zp)

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
  async def _fetch_parallel(self, *race_id: int) -> dict[int, ZPRaceSprint]:
    """Fetch sprint data in parallel using async requests.

    Args:
      *race_id: One or more race ID integers to fetch

    Returns:
      Dictionary mapping race IDs to their sprint data
    """
    # SECURITY: Validate all race IDs before creating session
    # This avoids expensive login/session creation for invalid IDs
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

    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching sprint data for {len(race_id)} race(s)')

      # Build list of fetch tasks
      fetch_tasks = []
      for rid in validated_ids:
        url = f'{self._url}{rid}'
        fetch_tasks.append(session.fetch_json(url))

      # Execute all fetches in parallel

      results_raw: dict[int, str] = {}

      results_fetched: dict[int, ZPRaceSprint] = {}

      async def fetch_and_store(
        idx: int,
        task: Coroutine[Any, Any, str],
      ) -> None:
        """Helper to fetch and store result."""
        try:
          raw_json = await task
          race_id = validated_ids[idx]
          results_raw[race_id] = raw_json

          # Parse for fetched dict
          parsed = parse_json_safe(raw_json, context=f'sprint {race_id}')
          sprint_dict = parsed if isinstance(parsed, dict) else {}
          results_fetched[race_id] = ZPRaceSprint.from_dict(sprint_dict)

          logger.debug(
            f'Successfully fetched sprint ID: {race_id}',
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
      logger.info(f'Successfully fetched {len(validated_ids)} race sprint(s)')

      # Share the session with primes to avoid second login
      self.primes.set_session(session)
      await self.primes.afetch(*validated_ids)
      self.extract_banners()
      self.enrich_sprints()

      return self._fetched

    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  def extract_banners(self) -> list[dict[str, Any]]:
    """Extract sprint_id and name from primes data to build banner list.

    Loops through the primes._fetched ZPPrime objects and extracts sprint_id
    and name from prime segments to create a list of banner dictionaries.

    Returns:
      List of dictionaries with sprint_id and name keys

    Example:
      [
        {"sprint_id": 68, "name": "Sprint 1"},
        {"sprint_id": 72, "name": "Sprint 2"}
      ]
    """
    logger.debug('Extracting banners from primes data')
    banners: list[dict[str, Any]] = []

    # Loop through primes._fetched: race_id -> ZPPrime object
    for race_id, prime_obj in self.primes._fetched.items():
      logger.debug(f'Processing race ID: {race_id}')

      # Iterate through the ZPPrime object (Sequence protocol)
      # This gives us all ZPPrimeSegment objects
      for segment in prime_obj:
        # Extract sprint_id and name from segment
        if segment.sprint_id and segment.name:
          banner = {
            'sprint_id': str(segment.sprint_id),
            'name': segment.name,
          }
          # Avoid duplicates
          if banner not in banners:
            banners.append(banner)
            logger.debug(f'Added banner: {banner}')

    self.banners = banners
    logger.info(f'Extracted {len(banners)} unique banner(s)')
    logger.debug(f'{banners}')
    return self.banners

  # ----------------------------------------------------------------------------
  def enrich_sprints(self) -> dict[Any, Any]:
    """Enrich sprint data by replacing sprint IDs with banner names in performance dicts.

    For each rider in the fetched sprint data, replace numeric sprint IDs in the
    msec, watts, and wkg dicts with their corresponding sprint names from banners.
    Also populates sprint_names for direct lookup.

    Returns:
      Dictionary with enriched sprint data (self._fetched, modified in place)
    """
    logger.debug('Enriching sprint data with banner names')

    # Create sprint_id to name mapping for quick lookup
    id_to_name: dict[str, str] = {}
    for banner in self.banners:
      sprint_id = str(banner['sprint_id'])
      name = banner['name']
      id_to_name[sprint_id] = name
      logger.debug(f'Mapping sprint_id {sprint_id} -> {name}')

    # Process each race (modify self._fetched in place)
    for race_id, race_data in self._fetched.items():
      logger.debug(f'Processing race ID: {race_id}')

      # race_data is a ZPRaceSprint object
      if isinstance(race_data, ZPRaceSprint):
        # Iterate through all riders in this race
        for rider in race_data:
          if isinstance(rider, ZPRiderSprint):
            # Update sprint names in the sprints list
            for sprint in rider.sprints:
              sprint_id = sprint.get('name', '')
              if sprint_id in id_to_name:
                sprint['name'] = id_to_name[sprint_id]
                logger.debug(
                  f'Replaced sprint_id {sprint_id} with {sprint["name"]}',
                )

            logger.debug(f'Enriched rider {rider.zwift_id}')

    # Update processed with enriched data
    self.processed = self._fetched
    logger.info(f'Enriched sprint data for {len(self._fetched)} race(s)')
    return self._fetched

  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  def _fetch_sequential(self, *race_id: int) -> dict[int, ZPRaceSprint]:
    """Fetch sprints data sequentially (synchronous mode).

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
      f'Fetching sprints data in synchronous mode for {len(race_id)} ID(s)',
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
    results_fetched: dict[int, ZPRaceSprint] = {}

    # Fetch each ID sequentially
    for id_val in validated_ids:
      logger.debug(f'Fetching sprints data for race ID: {id_val}')
      url = f'{self._url}{id_val}'

      # Synchronous blocking call
      raw_json = zp.fetch_json(url)
      results_raw[id_val] = raw_json

      # Parse immediately (no parallel parsing)
      parsed = parse_json_safe(raw_json, context=f'sprints {id_val}')
      sprint_dict = parsed if isinstance(parsed, dict) else {}
      results_fetched[id_val] = ZPRaceSprint.from_dict(sprint_dict)

      logger.debug(f'Successfully fetched sprints data for race ID: {id_val}')

    self._raw = results_raw

    self._fetched = results_fetched

    self.processed = {}  # Reserved for future use

    logger.info(
      f'Successfully fetched {len(validated_ids)} sprints(s) in sync mode',
    )

    # Fetch primes data and enrich sprints with banner names
    self.primes.set_zp_session(zp)
    self.primes.fetch(*validated_ids)
    self.extract_banners()
    self.enrich_sprints()

    return self._fetched

  @classmethod
  def set_sync_mode(cls, enabled: bool) -> None:
    """Enable or disable synchronous fetch mode.

    Args:
      enabled: True to enable sync mode, False for async (default)
    """
    cls._sync_mode = enabled
    mode = 'synchronous' if enabled else 'asynchronous (parallel)'
    logger.info(f'Sprints fetch mode set to: {mode}')

  def fetch(self, *race_id: int) -> dict[int, ZPRaceSprint]:
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
  async def afetch(self, *race_id: int) -> dict[int, ZPRaceSprint]:
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

  # ----------------------------------------------------------------------------
  def json(self) -> str:
    """Return JSON string representation of fetched data.

    Converts ZPRaceSprint objects to dicts before serialization.

    Returns:
      JSON-formatted string of all fetched sprint data
    """
    serializable = {
      key: value.asdict() if isinstance(value, ZPRaceSprint) else value
      for key, value in self._fetched.items()
    }
    return json.JSONEncoder(indent=2).encode(serializable)


# ==============================================================================
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

  x = ZPSprintsFetch()

  x.fetch(*args.race_id)

  if args.raw:
    print(x.raw)


# ==============================================================================
if __name__ == '__main__':
  main()
