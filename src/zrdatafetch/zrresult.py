"""Unified ZRResult class with both sync and async fetch capabilities.

This module provides the ZRResult class for fetching and storing race result
data from the Zwiftracing API, including per-rider finishes and rating changes.
"""

from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.exceptions import ZRConfigError, ZRNetworkError
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
  """

  # Public attributes (in __init__)
  race_id: int = 0
  results: list[ZRRiderResult] = field(default_factory=list)

  # Private attributes (not in __init__)
  _raw: dict = field(default_factory=dict, init=False, repr=False)
  _race: dict = field(default_factory=dict, init=False, repr=False)
  _verbose: bool = field(default=False, init=False, repr=False)
  _zr: AsyncZR_obj | None = field(default=None, init=False, repr=False)

  # -----------------------------------------------------------------------
  def set_session(self, zr: AsyncZR_obj) -> None:
    """Set the AsyncZR_obj session to use for async fetching.

    Args:
      zr: AsyncZR_obj instance to use for API requests
    """
    self._zr = zr

  # -----------------------------------------------------------------------
  def fetch(self, race_id: int | None = None) -> None:
    """Fetch race result data from the Zwiftracing API (synchronous).

    Fetches all rider results for a specific race ID from the Zwiftracing API.

    Args:
      race_id: The race ID to fetch (uses self.race_id if not provided)

    Raises:
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      result = ZRResult()
      result.fetch(race_id=3590800)
      print(result.json())
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
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(f'Fetching results for race_id={self.race_id}')

    # Endpoint is /public/results/{race_id}
    endpoint = f'/public/results/{self.race_id}'

    # Fetch JSON from API
    headers = {'Authorization': config.authorization}
    try:
      self._raw = self.fetch_json(endpoint, headers=headers)
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch race result: {e}')
      raise

    # Parse response
    self._parse_response()

  # -----------------------------------------------------------------------
  async def afetch(self, race_id: int | None = None) -> None:
    """Fetch race result data from the Zwiftracing API (asynchronous).

    Fetches all rider results for a specific race ID from the Zwiftracing API.

    Args:
      race_id: The race ID to fetch (uses self.race_id if not provided)

    Raises:
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      result = ZRResult()
      result.set_session(zr)
      await result.afetch(race_id=3590800)
      print(result.json())
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
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(f'Fetching results for race_id={self.race_id} (async)')

    # Create temporary session if none provided
    if not self._zr:
      self._zr = AsyncZR_obj()
      await self._zr.init_client()
      owns_session = True
    else:
      owns_session = False

    try:
      # Endpoint is /public/results/{race_id}
      endpoint = f'/public/results/{self.race_id}'

      # Fetch JSON from API
      headers = {'Authorization': config.authorization}
      self._raw = await self._zr.fetch_json(endpoint, headers=headers)

      # Parse response
      self._parse_response()
      logger.info(f'Successfully fetched results for race_id={self.race_id}')
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch race result: {e}')
      raise
    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zr:
        await self._zr.close()

  # -----------------------------------------------------------------------
  def _parse_response(self) -> None:
    """Parse API response into result objects.

    Extracts rider results from the raw API response and creates ZRRiderResult
    objects for each participant. Silently handles missing or malformed data.
    """
    if not self._raw:
      logger.warning('No data to parse')
      return

    self._race = self._raw

    # Check for error in response
    if isinstance(self._race, dict) and 'message' in self._race:
      logger.error(f"API error: {self._race['message']}")
      return

    # Response should be a list of rider results
    if not isinstance(self._race, list):
      logger.warning('Expected list of results, got different format')
      return

    try:
      for rider_data in self._race:
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
