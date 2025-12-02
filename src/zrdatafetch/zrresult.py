"""Unified ZRResult class with both sync and async fetch capabilities.

This module provides the ZRResult class for fetching and storing race result
data from the Zwiftracing API, including per-rider finishes and rating changes.
"""

import asyncio
from dataclasses import asdict, dataclass, field
from typing import Any

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr import ZR_obj

logger = get_logger(__name__)


# ===============================================================================
@dataclass
class ZRRiderResult:
  """Individual rider result from a Zwiftracing race.

  Represents a single rider's performance and rating change in a race result.

  Attributes:
    zwift_id: Rider's Zwift ID
    position: Finishing position in the race
    position_in_category: Position within their category
    category: Category (e.g., A, B, C, D)
    time: Finish time in seconds (for timed races)
    gap: Time gap from first place in seconds
    rating_before: Rating before the race
    rating: Rating after the race
    rating_delta: Change in rating from the race
  """

  zwift_id: int = 0
  position: int = 0
  position_in_category: int = 0
  category: str = ''
  time: float = 0.0
  gap: float = 0.0
  rating_before: float = 0.0
  rating: float = 0.0
  rating_delta: float = 0.0

  def to_dict(self) -> dict[str, Any]:
    """Return dictionary representation of rider result.

    Returns:
      Dictionary with all attributes
    """
    return asdict(self)


# ===============================================================================
@dataclass
class ZRResult(ZR_obj):
  """Race result data from Zwiftracing API.

  Represents all rider results from a specific race, including the race ID
  and a list of individual rider results with rating changes. Supports both
  synchronous and asynchronous operations.

  Synchronous usage:
    result = ZRResult()
    result.fetch(race_id=3590800)
    print(result.json())

  Asynchronous usage:
    async with AsyncZR_obj() as zr:
      result = ZRResult()
      result.set_session(zr)
      await result.afetch(race_id=3590800)
      print(result.json())

  Attributes:
    race_id: The race ID (Zwift event ID)
    results: List of ZRRiderResult objects for each participant
    _raw: Raw JSON response string from API (unprocessed, for debugging)
    _race: Parsed race data dictionary (internal)

  Note:
    The _raw attribute stores the original JSON string response from the
    API before any parsing or validation. This ensures we always have
    access to the exact data received for debugging and logging purposes.
  """

  # Public attributes (in __init__)
  race_id: int = 0
  results: list[ZRRiderResult] = field(default_factory=list)

  # Private attributes (not in __init__)
  _raw: str = field(default='', init=False, repr=False)
  _race: dict = field(default_factory=dict, init=False, repr=False)
  _verbose: bool = field(default=False, init=False, repr=False)
  _zr: AsyncZR_obj | None = field(default=None, init=False, repr=False)
  _zr_sync: ZR_obj | None = field(default=None, init=False, repr=False)

  # -----------------------------------------------------------------------
  def set_session(self, zr: AsyncZR_obj) -> None:
    """Set the AsyncZR_obj session to use for async fetching.

    Args:
      zr: AsyncZR_obj instance to use for API requests
    """
    self._zr = zr

  # -----------------------------------------------------------------------
  def set_zr_session(self, zr: ZR_obj) -> None:
    """Set the ZR_obj session to use for fetching.

    Session will be converted to async for internal use.

    Args:
      zr: ZR_obj instance to use for API requests
    """
    self._zr_sync = zr

  # -----------------------------------------------------------------------
  async def _get_or_create_session(self) -> tuple[AsyncZR_obj, bool]:
    """Get or create an async session for fetching.

    Returns:
      Tuple of (AsyncZR_obj session, owns_session flag)
      If owns_session is True, caller must close the session
    """
    # Case 1: Use existing async session
    if self._zr:
      return (self._zr, False)

    # Case 2: Have sync session - create new async session
    # Note: ZR doesn't use cookies like ZP, so we just create a new async session
    if self._zr_sync:
      async_zr = AsyncZR_obj()
      await async_zr.init_client()
      return (async_zr, True)

    # Case 3: Create temporary session
    temp_zr = AsyncZR_obj()
    await temp_zr.init_client()
    return (temp_zr, True)

  # -----------------------------------------------------------------------
  async def _afetch_internal(self, race_id: int | None = None) -> None:
    """Internal async fetch implementation.

    Args:
      race_id: The race ID to fetch (uses self.race_id if not provided)
    """

    # Use provided value or default
    if race_id is not None:
      self.race_id = race_id

    if self.race_id == 0:
      logger.warning('No race_id provided for fetch')
      return

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    session, owns_session = await self._get_or_create_session()

    try:
      logger.debug(f'Fetching results for race_id={self.race_id}')

      # Endpoint is /public/results/{race_id}
      endpoint = f'/public/results/{self.race_id}'

      # Fetch JSON from API
      headers = {'Authorization': config.authorization}
      self._raw = await session.fetch_json(endpoint, headers=headers)

      # Parse response
      self._parse_response()
      logger.info(f'Successfully fetched results for race_id={self.race_id}')
    except NetworkError as e:
      logger.error(f'Failed to fetch race result: {e}')
      raise
    finally:
      if owns_session:
        await session.close()

  # -----------------------------------------------------------------------
  def fetch(self, race_id: int | None = None) -> None:
    """Fetch race result data from the Zwiftracing API (synchronous interface).

    Uses async implementation internally for consistency and efficiency.
    Fetches all rider results for a specific race ID from the Zwiftracing API.

    Args:
      race_id: The race ID to fetch (uses self.race_id if not provided)

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured
      RuntimeError: If called from async context (use afetch() instead)

    Example:
      result = ZRResult()
      result.fetch(race_id=3590800)
      print(result.json())
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
      asyncio.run(self._afetch_internal(race_id))

  # -----------------------------------------------------------------------
  async def afetch(self, race_id: int | None = None) -> None:
    """Fetch race result data from the Zwiftracing API (asynchronous interface).

    Uses shared internal async implementation. Supports session sharing
    via set_session() or set_zr_session().

    Args:
      race_id: The race ID to fetch (uses self.race_id if not provided)

    Raises:
      NetworkError: If the API request fails
      ConfigError: If authorization is not configured

    Example:
      result = ZRResult()
      result.set_session(zr)
      await result.afetch(race_id=3590800)
      print(result.json())
    """
    await self._afetch_internal(race_id)

  # -----------------------------------------------------------------------
  def _parse_response(self) -> None:
    """Parse raw JSON string from _raw into structured result objects.

    Converts the raw JSON string stored in self._raw into a Python dict
    (self._race), then extracts individual rider results into ZRRiderResult
    objects. Handles malformed JSON and missing fields gracefully.

    The parsing is separated from fetching to ensure _raw always contains
    the unprocessed response for debugging/logging purposes.

    Side effects:
      - Sets self._race to parsed dict
      - Populates self.results list with ZRRiderResult objects

    The API response format is a dictionary with metadata and a 'results' array:
    {
      'eventId': '4613373',
      'time': 1733339700,
      'routeId': '3356878261',
      'distance': 16.22,
      'title': 'DRS Winter Warriors - Metals',
      'type': 'Race',
      'subType': 'Points',
      'results': [...]
    }
    """
    if not self._raw:
      logger.warning('No data to parse')
      return

    # Parse JSON string to dict
    parsed = parse_json_safe(self._raw, context=f'race result {self.race_id}')
    if not isinstance(parsed, dict):
      logger.error(f'Expected dict for race result data, got {type(parsed).__name__}')
      return

    self._race = parsed

    # Check for error in response
    if 'message' in self._race:
      logger.error(f"API error: {self._race['message']}")
      return

    # Response should be a dict with a 'results' key
    if 'results' not in self._race:
      logger.warning('Expected dict with results key, missing in response')
      return

    # Validate that we have the expected race_id
    event_id = self._race.get('eventId')
    if event_id and str(event_id) != str(self.race_id):
      logger.warning(
        f'Event ID mismatch: expected {self.race_id}, got {event_id}',
      )

    # Extract the results array
    results_data = self._race.get('results', [])
    if not results_data:
      logger.warning('No results found in response')
      return

    try:
      for rider_data in results_data:
        try:
          result = ZRRiderResult(
            zwift_id=rider_data.get('riderId', 0),
            position=rider_data.get('position', 0),
            position_in_category=rider_data.get('positionInCategory', 0),
            category=rider_data.get('category', ''),
            time=float(rider_data.get('time', 0.0)),
            gap=float(rider_data.get('gap', 0.0)),
            rating_before=float(rider_data.get('ratingBefore', 0.0)),
            rating=float(rider_data.get('rating', 0.0)),
            rating_delta=float(rider_data.get('ratingDelta', 0.0)),
          )
          self.results.append(result)
        except (KeyError, TypeError, ValueError) as e:
          logger.warning(f'Skipping malformed rider result: {e}')
          continue

      logger.debug(
        f'Successfully parsed {len(self.results)} race results for race_id={self.race_id}',
      )
    except Exception as e:
      logger.error(f'Error parsing response: {e}')

  # -----------------------------------------------------------------------
  def to_dict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with all public attributes and results as dicts
    """
    return {
      'race_id': self.race_id,
      'results': [r.to_dict() for r in self.results],
    }
