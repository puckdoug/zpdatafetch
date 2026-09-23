"""Unified League class with both sync and async fetch capabilities."""

import asyncio
import json
from argparse import ArgumentParser
from typing import Any

import anyio

from shared.validation import ValidationError, validate_id_list
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.logging_config import get_logger, setup_logging
from zpdatafetch.zp import ZP
from zpdatafetch.zp_obj import ZP_obj
from zpdatafetch.zp_utils import extract_numeric
from zpdatafetch.zpleague import ZPLeague

logger = get_logger(__name__)


# ==============================================================================
def _parse_source(raw: str, name: str, league_id: int) -> Any:
  """Parse a league source response, rejecting non-JSON bodies.

  Args:
    raw: Raw response text
    name: Source name (standings, team_standings, team_event_results, events)
    league_id: League ID for error messages

  Returns:
    Parsed dict (standings) or list (the other sources)

  Raises:
    ValueError: If the response is not valid JSON
  """
  try:
    parsed = json.loads(raw)
  except json.JSONDecodeError as e:
    hint = ' (looks like HTML, not JSON)' if raw.lstrip().startswith('<') else ''
    raise ValueError(
      f'league {league_id} {name}: response is not JSON{hint}',
    ) from e
  if name == 'standings':
    return parsed if isinstance(parsed, dict) else {}
  if isinstance(parsed, dict):
    data = parsed.get('data', [])
    return data if isinstance(data, list) else []
  if isinstance(parsed, list):
    return parsed
  return []


# Named per-league sources, in fetch order
_LEAGUE_SOURCES: tuple[str, ...] = (
  'standings',
  'team_standings',
  'team_event_results',
  'events',
)


# ==============================================================================
class ZPLeagueFetch(ZP_obj):
  """Fetches and stores league standing data from Zwiftpower.

  Retrieves league standings using league IDs. Supports both synchronous
  and asynchronous operations.

  Synchronous usage:
    league = ZPLeagueFetch()
    league.fetch(1234, 5678)
    print(league.json())

  Asynchronous usage:
    async with AsyncZP() as zp:
      league = ZPLeagueFetch()
      league.set_session(zp)
      await league.afetch(1234, 5678)
      print(league.json())

  Attributes:
    raw: Dictionary mapping league IDs to their standings data
    verbose: Enable verbose output for debugging
  """

  _url: str = 'https://zwiftpower.com/cache3/global/'
  _url_prefix: str = 'league_standings_'
  _url_end: str = '.json'
  _sync_mode: bool = False  # Class-level sync mode flag

  # Additional league data sources
  _team_standings_url: str = (
    'https://zwiftpower.com/cache3/global/league_team_standings_'
  )
  _events_url: str = (
    'https://zwiftpower.com/api3.php?do=league_event_results&id='
  )
  _team_event_standings_url: str = (
    'https://zwiftpower.com/api3.php?do=league_team_event_standings&id='
  )
  _league_list_url: str = 'https://zwiftpower.com/api3.php?do=league_list'

  def __init__(self) -> None:
    """Initialize a new League instance."""
    super().__init__()
    self._fetched: dict[int, ZPLeague] = {}  # Override type to use ZPLeague
    self._zp: AsyncZP | None = None  # Async session
    self._zp_sync: ZP | None = None  # Sync session (for reference only)

    # Raw responses for the non-standings league sources
    self._team_standings_raw: dict[int, str] = {}
    self._team_event_results_raw: dict[int, str] = {}
    self._events_raw: dict[int, str] = {}
    self._league_list_raw: str = ''

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
  def json(self) -> str:
    """Serialize the fetched data to formatted JSON string.

    Converts ZPLeague objects to dicts before serialization.

    Returns:
      JSON string with 2-space indentation
    """
    # Convert ZPLeague objects to dicts
    serializable = {
      key: value.asdict() if isinstance(value, ZPLeague) else value
      for key, value in self._fetched.items()
    }
    return json.JSONEncoder(indent=2).encode(serializable)

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
  async def _fetch_parallel(self, *league_id: int) -> dict[int, ZPLeague]:
    """Fetch league data in parallel using async requests.

    Fetches rider standings, team standings, team-event standings, and
    events for each league, plus the league catalog once for metadata.
    Sources are independent: a failure in one logs a warning and leaves
    that collection empty. Raises only if every per-league source fails.

    Args:
      *league_id: One or more league ID integers to fetch

    Returns:
      Dictionary mapping league IDs to ZPLeague objects
    """
    # SECURITY: Validate all league IDs before creating session
    # This avoids expensive login/session creation for invalid IDs
    try:
      validated_ids = validate_id_list(list(league_id), id_type='league')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    session, owns_session = await self._get_or_create_session()

    try:
      logger.info(f'Fetching league data for {len(league_id)} ID(s)')

      league_info_map = await self._fetch_league_catalog_async(session)

      results_raw: dict[int, str] = {}
      results_fetched: dict[int, ZPLeague] = {}
      self._team_standings_raw = {}
      self._team_event_results_raw = {}
      self._events_raw = {}

      async def fetch_league(idx: int) -> None:
        """Fetch all sources for one league; raise only if all fail."""
        lid = validated_ids[idx]
        raws, parsed_sources, errors = await self._fetch_league_sources_async(
          session,
          lid,
        )

        if len(errors) == len(_LEAGUE_SOURCES):
          logger.error(f'League {lid}: all sources failed')
          raise errors[0][1]

        if 'standings' in raws:
          results_raw[lid] = raws['standings']
        if 'team_standings' in raws:
          self._team_standings_raw[lid] = raws['team_standings']
        if 'team_event_results' in raws:
          self._team_event_results_raw[lid] = raws['team_event_results']
        if 'events' in raws:
          self._events_raw[lid] = raws['events']

        results_fetched[lid] = self._build_league(
          lid,
          parsed_sources,
          league_info_map.get(lid),
        )
        logger.debug(f'Successfully fetched league ID: {lid}')

      async with anyio.create_task_group() as tg:
        for idx in range(len(validated_ids)):
          tg.start_soon(fetch_league, idx)

      self._raw = results_raw
      self._fetched = results_fetched
      self.processed = {}  # Reserved for future use
      logger.info(f'Successfully fetched {len(validated_ids)} league(s)')

      return self._fetched

    finally:
      if owns_session:
        await session.close()

  # ----------------------------------------------------------------------------
  async def _fetch_league_catalog_async(
    self,
    session: AsyncZP,
  ) -> dict[int, dict[str, Any]]:
    """Fetch the league catalog once and index it by league id."""
    league_info_map: dict[int, dict[str, Any]] = {}
    self._league_list_raw = ''
    try:
      raw_list = await session.fetch_json(self._league_list_url)
      self._league_list_raw = raw_list
      rows = _parse_source(raw_list, 'league_list', 0)
      for row in rows:
        if isinstance(row, dict):
          lid = extract_numeric(row.get('league_id'), int, 0)
          if lid:
            league_info_map[lid] = row
    except Exception as e:
      logger.warning(f'League catalog fetch failed (metadata skipped): {e}')
    return league_info_map

  # ----------------------------------------------------------------------------
  async def _fetch_league_sources_async(
    self,
    session: AsyncZP,
    lid: int,
  ) -> tuple[dict[str, str], dict[str, Any], list[tuple[str, Exception]]]:
    """Fetch and parse each per-league source; collect failures."""
    raws: dict[str, str] = {}
    parsed_sources: dict[str, Any] = {}
    errors: list[tuple[str, Exception]] = []
    for name in _LEAGUE_SOURCES:
      url = self._source_url(name, lid)
      try:
        raw = await session.fetch_json(url)
        parsed_sources[name] = _parse_source(raw, name, lid)
        raws[name] = raw
      except Exception as e:
        errors.append((name, e))
        logger.warning(f'League {lid}: {name} fetch failed: {e}')
    return raws, parsed_sources, errors

  # ----------------------------------------------------------------------------
  def _source_url(self, name: str, lid: int) -> str:
    """Build the URL for a named league source."""
    if name == 'standings':
      return f'{self._url}{self._url_prefix}{lid}{self._url_end}'
    if name == 'team_standings':
      return f'{self._team_standings_url}{lid}{self._url_end}'
    if name == 'team_event_results':
      return f'{self._team_event_standings_url}{lid}&zwift_event_id='
    if name == 'events':
      return f'{self._events_url}{lid}'
    raise ValueError(f'Unknown league source: {name}')

  # ----------------------------------------------------------------------------
  def _build_league(
    self,
    lid: int,
    parsed_sources: dict[str, Any],
    league_info: dict[str, Any] | None,
  ) -> ZPLeague:
    """Build a ZPLeague from the successfully parsed sources."""
    standings = parsed_sources.get('standings')
    standings_dict = standings if isinstance(standings, dict) else {}
    return ZPLeague.from_dict(
      standings_dict,
      league_id=lid,
      events=parsed_sources.get('events'),
      team_standings=parsed_sources.get('team_standings'),
      team_event_results=parsed_sources.get('team_event_results'),
      league_info=league_info,
    )

  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  # ----------------------------------------------------------------------------
  def _fetch_sequential(self, *league_id: int) -> dict[int, ZPLeague]:
    """Fetch league data sequentially (synchronous mode).

    This method provides a clear, separate execution path for debugging.
    All requests are made synchronously in sequence, with no parallelization.
    Sources are independent: a failure in one logs a warning and leaves
    that collection empty. Raises only if every per-league source fails.

    Args:
      *league_id: One or more league ID integers to fetch

    Returns:
      Dictionary mapping league IDs to ZPLeague objects

    Raises:
      ValueError: If any ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    logger.info(
      f'Fetching league data in synchronous mode for {len(league_id)} ID(s)',
    )

    # SECURITY: Validate all IDs before processing
    try:
      validated_ids = validate_id_list(list(league_id), id_type='league')
    except ValidationError as e:
      logger.error(f'ID validation failed: {e}')
      raise

    # Use a provided session or create and authenticate one
    zp = self._zp_sync
    if zp is None:
      zp = ZP()
      zp.login()

    league_info_map = self._fetch_league_catalog_sync(zp)

    results_raw: dict[int, str] = {}
    results_fetched: dict[int, ZPLeague] = {}
    self._team_standings_raw = {}
    self._team_event_results_raw = {}
    self._events_raw = {}

    # Fetch each ID sequentially
    for id_val in validated_ids:
      logger.debug(f'Fetching league data for league ID: {id_val}')
      raws, parsed_sources, errors = self._fetch_league_sources_sync(
        zp,
        id_val,
      )

      if len(errors) == len(_LEAGUE_SOURCES):
        logger.error(f'League {id_val}: all sources failed')
        raise errors[0][1]

      if 'standings' in raws:
        results_raw[id_val] = raws['standings']
      if 'team_standings' in raws:
        self._team_standings_raw[id_val] = raws['team_standings']
      if 'team_event_results' in raws:
        self._team_event_results_raw[id_val] = raws['team_event_results']
      if 'events' in raws:
        self._events_raw[id_val] = raws['events']

      results_fetched[id_val] = self._build_league(
        id_val,
        parsed_sources,
        league_info_map.get(id_val),
      )
      logger.debug(f'Successfully fetched league data for league ID: {id_val}')

    self._raw = results_raw

    self._fetched = results_fetched

    self.processed = {}  # Reserved for future use

    logger.info(
      f'Successfully fetched {len(validated_ids)} league(s) in sync mode',
    )
    return self._fetched

  # ----------------------------------------------------------------------------
  def _fetch_league_catalog_sync(
    self,
    zp: ZP,
  ) -> dict[int, dict[str, Any]]:
    """Fetch the league catalog once (sync) and index it by league id."""
    league_info_map: dict[int, dict[str, Any]] = {}
    self._league_list_raw = ''
    try:
      raw_list = zp.fetch_json(self._league_list_url)
      self._league_list_raw = raw_list
      rows = _parse_source(raw_list, 'league_list', 0)
      for row in rows:
        if isinstance(row, dict):
          lid = extract_numeric(row.get('league_id'), int, 0)
          if lid:
            league_info_map[lid] = row
    except Exception as e:
      logger.warning(f'League catalog fetch failed (metadata skipped): {e}')
    return league_info_map

  # ----------------------------------------------------------------------------
  def _fetch_league_sources_sync(
    self,
    zp: ZP,
    lid: int,
  ) -> tuple[dict[str, str], dict[str, Any], list[tuple[str, Exception]]]:
    """Fetch and parse each per-league source (sync); collect failures."""
    raws: dict[str, str] = {}
    parsed_sources: dict[str, Any] = {}
    errors: list[tuple[str, Exception]] = []
    for name in _LEAGUE_SOURCES:
      url = self._source_url(name, lid)
      try:
        raw = zp.fetch_json(url)
        parsed_sources[name] = _parse_source(raw, name, lid)
        raws[name] = raw
      except Exception as e:
        errors.append((name, e))
        logger.warning(f'League {lid}: {name} fetch failed: {e}')
    return raws, parsed_sources, errors

  @classmethod
  def set_sync_mode(cls, enabled: bool) -> None:
    """Enable or disable synchronous fetch mode.

    Args:
      enabled: True to enable sync mode, False for async (default)
    """
    cls._sync_mode = enabled
    mode = 'synchronous' if enabled else 'asynchronous (parallel)'
    logger.info(f'League fetch mode set to: {mode}')

  def fetch(self, *league_id: int) -> dict[int, ZPLeague]:
    """Fetch league data for one or more league IDs (synchronous).

    Retrieves the league standings from Zwiftpower cache.
    Stores results in the raw dictionary keyed by league ID.

    Args:
      *league_id: One or more league ID integers to fetch

    Returns:
      Dictionary mapping league IDs to ZPLeague objects

    Raises:
      ValueError: If any league ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    # Check if sync mode is enabled
    if self._sync_mode:
      return self._fetch_sequential(*league_id)

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
      return asyncio.run(self._fetch_parallel(*league_id))

  # ----------------------------------------------------------------------------
  async def afetch(self, *league_id: int) -> dict[int, ZPLeague]:
    """Fetch league data for one or more league IDs (asynchronous interface).

    Uses parallel async requests internally. Supports session sharing
    via set_session() or set_zp_session().

    Args:
      *league_id: One or more league ID integers to fetch

    Returns:
      Dictionary mapping league IDs to ZPLeague objects

    Raises:
      ValueError: If any league ID is invalid
      NetworkError: If network requests fail
      AuthenticationError: If authentication fails
    """
    return await self._fetch_parallel(*league_id)


# ==============================================================================
def main() -> None:
  p = ArgumentParser(
    description='Module for fetching league data using the Zwiftpower API',
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
  p.add_argument('league_id', type=int, nargs='+', help='a list of league_ids')
  args = p.parse_args()

  # Configure logging based on verbosity level (output to stderr)
  if args.verbose >= 2:
    setup_logging(console_level='DEBUG', force_console=True)
  elif args.verbose == 1:
    setup_logging(console_level='INFO', force_console=True)

  x = ZPLeagueFetch()

  x.fetch(*args.league_id)

  if args.raw:
    print(x.raw)


# ==============================================================================
if __name__ == '__main__':
  main()
