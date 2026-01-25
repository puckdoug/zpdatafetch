"""Zwift RideOn data fetching and management.

Provides access to RideOn data from Zwift's unofficial API, including
fetching RideOns received on activities and giving RideOns.
"""

import json
from typing import Any

import httpx

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zdatafetch.auth import ZwiftAuth
from zdatafetch.config import Config
from zdatafetch.logging_config import get_logger

logger = get_logger(__name__)


class ZwiftRideOns:
  """Zwift RideOn data.

  Represents RideOns received on an activity from Zwift's unofficial API.
  Also supports giving RideOns to activities.

  API Endpoints:
      GET https://us-or-rly101.zwift.com/api/profiles/{riderId}/activities/{activityId}/rideons
      POST https://us-or-rly101.zwift.com/api/profiles/{riderId}/activities/{activityId}/rideon

  Documentation: https://github.com/strukturunion-mmw/zwift-api-documentation

  Synchronous usage:
      rideons = ZwiftRideOns()
      rideons.fetch(550564, 12345678)
      print(f"RideOns: {rideons.rideon_count()}")
      print(rideons)  # Pretty print all data

  Batch usage:
      rideons_data = ZwiftRideOns.fetch_multiple((550564, 12345), (550564, 67890))
      for key, data in rideons_data.items():
          print(f"Activity {key}: {data.rideon_count()} RideOns")

  Giving RideOns:
      success = ZwiftRideOns.give_rideon(550564, 12345678)
      if success:
          print("RideOn given!")

  Attributes:
      rider_id: Rider ID for this activity
      activity_id: Activity ID for this data
      rideons: List of rider objects who gave RideOns
  """

  BASE_URL = 'https://us-or-rly101.zwift.com'

  def __init__(self) -> None:
    """Initialize empty RideOn data (no auth parameter).

    Credentials are loaded from Config at fetch time.
    """
    self._raw: str = ''  # Raw JSON response
    self._fetched: dict[str, Any] = {}  # Parsed data
    self.processed: dict = {}  # Reserved for future use

    # Populated after fetch
    self.rider_id: int = 0
    self.activity_id: int = 0
    self.rideons: list[dict[str, Any]] = []

  def fetch(self, rider_id: int, activity_id: int) -> None:
    """Fetch RideOn data for a single activity.

    Loads credentials from Config, authenticates, fetches data,
    and populates instance attributes.

    Args:
        rider_id: Zwift rider ID who owns the activity
        activity_id: Activity ID to fetch RideOns for

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails
        AuthenticationError: If authentication fails
    """
    # Load credentials from config
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(
      f'Fetching RideOns for activity {activity_id} (rider {rider_id})'
    )

    # Authenticate
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch data
    self.rider_id = rider_id
    self.activity_id = activity_id

    url = f'{self.BASE_URL}/api/profiles/{rider_id}/activities/{activity_id}/rideons'

    try:
      with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=30.0)

        if response.status_code == 404:
          raise NetworkError(
            f'Activity {activity_id} not found for rider {rider_id}',
          )
        if response.status_code != 200:
          raise NetworkError(
            f'Failed to fetch RideOns for activity {activity_id}: '
            f'HTTP {response.status_code} - {response.text}',
          )

        # Store raw response
        self._raw = response.text

        # Parse and populate attributes
        self._parse_response()
        logger.info(
          f'Successfully fetched RideOns for activity {activity_id} (rider {rider_id})',
        )

    except httpx.TimeoutException as e:
      raise NetworkError(
        f'Request timed out fetching RideOns for activity {activity_id}: {e}',
      ) from e
    except httpx.HTTPError as e:
      raise NetworkError(
        f'Network error fetching RideOns for activity {activity_id}: {e}',
      ) from e

  @classmethod
  def fetch_multiple(
    cls,
    *activity_tuples: tuple[int, int],
  ) -> dict[tuple[int, int], 'ZwiftRideOns']:
    """Fetch multiple activities' RideOns, returning dict of objects.

    Args:
        *activity_tuples: Tuples of (rider_id, activity_id) to fetch

    Returns:
        Dictionary mapping (rider_id, activity_id) tuples to ZwiftRideOns objects

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails

    Example:
        rideons_data = ZwiftRideOns.fetch_multiple((550564, 12345), (550564, 67890))
        for (rider_id, activity_id), data in rideons_data.items():
            print(f"Activity {activity_id}: {data.rideon_count()} RideOns")
    """
    if not activity_tuples:
      logger.warning('No activity tuples provided for batch fetch')
      return {}

    # Load credentials once
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(
      f'Fetching RideOns for {len(activity_tuples)} activities in batch'
    )

    # Authenticate once
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch all RideOns
    results = {}
    with httpx.Client() as client:
      for rider_id, activity_id in activity_tuples:
        try:
          url = f'{cls.BASE_URL}/api/profiles/{rider_id}/activities/{activity_id}/rideons'
          response = client.get(url, headers=headers, timeout=30.0)

          if response.status_code == 200:
            rideons_obj = cls()
            rideons_obj.rider_id = rider_id
            rideons_obj.activity_id = activity_id
            rideons_obj._raw = response.text
            rideons_obj._parse_response()
            results[(rider_id, activity_id)] = rideons_obj
            logger.debug(
              f'Successfully fetched RideOns for activity {activity_id} '
              f'(rider {rider_id})',
            )
          else:
            logger.warning(
              f'Failed to fetch RideOns for activity {activity_id} '
              f'(rider {rider_id}): HTTP {response.status_code}',
            )

        except Exception as e:
          logger.error(
            f'Error fetching RideOns for activity {activity_id} '
            f'(rider {rider_id}): {e}',
          )
          continue

    logger.info(
      f'Successfully fetched {len(results)}/{len(activity_tuples)} RideOns in batch',
    )
    return results

  @staticmethod
  def give_rideon(rider_id: int, activity_id: int) -> bool:
    """Give a RideOn to an activity.

    Loads credentials, authenticates, and posts a RideOn.

    Args:
        rider_id: Zwift rider ID who owns the activity
        activity_id: Activity ID to give RideOn to

    Returns:
        True if RideOn was successfully given, False otherwise

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails
        AuthenticationError: If authentication fails
    """
    # Load credentials from config
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(f'Giving RideOn to activity {activity_id} (rider {rider_id})')

    # Authenticate
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # POST RideOn
    url = f'{ZwiftRideOns.BASE_URL}/api/profiles/{rider_id}/activities/{activity_id}/rideon'

    try:
      with httpx.Client() as client:
        response = client.post(url, headers=headers, timeout=30.0)

        if response.status_code in (200, 201, 204):
          logger.info(
            f'Successfully gave RideOn to activity {activity_id} (rider {rider_id})',
          )
          return True
        if response.status_code == 404:
          logger.error(
            f'Activity {activity_id} not found for rider {rider_id}',
          )
          return False
        logger.error(
          f'Failed to give RideOn to activity {activity_id}: '
          f'HTTP {response.status_code} - {response.text}',
        )
        return False

    except httpx.TimeoutException as e:
      logger.error(
        f'Request timed out giving RideOn to activity {activity_id}: {e}',
      )
      return False
    except httpx.HTTPError as e:
      logger.error(
        f'Network error giving RideOn to activity {activity_id}: {e}',
      )
      return False

  def _parse_response(self) -> None:
    """Parse raw JSON string into structured RideOn data.

    Populates instance attributes from parsed data.
    """
    if not self._raw:
      logger.warning('No data to parse')
      return

    parsed = parse_json_safe(self._raw, context='rideons')
    if not isinstance(parsed, list):
      logger.error(
        f'Expected list for RideOns data, got {type(parsed).__name__}'
      )
      self._fetched = {'rideons': []}
      self.rideons = []
      return

    self._fetched = {'rideons': parsed}
    self.rideons = parsed

    logger.debug(
      f'Successfully parsed {len(self.rideons)} RideOns for activity '
      f'{self.activity_id} (rider {self.rider_id})',
    )

  def rideon_count(self) -> int:
    """Return count of RideOns.

    Returns:
        Number of RideOns received on this activity
    """
    return len(self.rideons)

  def rideon_ids(self) -> list[int]:
    """Return list of rider IDs who gave RideOns.

    Returns:
        List of rider IDs who gave RideOns to this activity
    """
    return [r.get('id', 0) for r in self.rideons if 'id' in r]

  def has_rideon_from(self, rider_id: int) -> bool:
    """Check if specific rider gave a RideOn.

    Args:
        rider_id: Rider ID to check

    Returns:
        True if rider gave a RideOn, False otherwise
    """
    return rider_id in self.rideon_ids()

  def __getattr__(self, name: str) -> Any:  # noqa: ANN401
    """Allow attribute access to any field.

    Args:
        name: Field name

    Returns:
        Field value

    Raises:
        AttributeError: If field doesn't exist
    """
    if name.startswith('_'):
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      )
    try:
      return self._fetched[name]
    except KeyError:
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      ) from None

  def __getitem__(self, key: str) -> Any:  # noqa: ANN401
    """Allow dictionary-style access.

    Args:
        key: Field name

    Returns:
        Field value
    """
    return self._fetched[key]

  def __str__(self) -> str:
    """Return human-readable string with RideOn data.

    Returns:
        Formatted string showing RideOn data
    """
    if not self._fetched:
      return 'ZwiftRideOns(no data)'

    # Format all fields for display like profile.py does
    lines = [
      f'ZwiftRideOns(rider_id={self.rider_id}, activity_id={self.activity_id})'
    ]
    for key, value in self._fetched.items():
      lines.append(f'  {key}: {value!r},')
    lines.append(')')
    return '\n'.join(lines)

  def __repr__(self) -> str:
    """Return detailed representation showing all fields.

    Returns:
        String representation with all data
    """
    if not self._fetched:
      return 'ZwiftRideOns()'
    return (
      f'ZwiftRideOns(rider_id={self.rider_id}, '
      f'activity_id={self.activity_id}, '
      f'rideons={len(self.rideons)})'
    )

  def asdict(self) -> dict[str, Any]:
    """Return underlying data as dictionary.

    Returns:
        RideOn data dictionary
    """
    return self._fetched

  def raw(self) -> str:
    """Return raw JSON response string.

    Returns:
        Raw JSON string from response
    """
    return self._raw

  def fetched(self) -> dict[str, Any]:
    """Return parsed data dictionary.

    Returns:
        Parsed dictionary from the raw JSON response
    """
    return self._fetched

  def json(self) -> str:
    """Serialize RideOn data to formatted JSON string.

    Returns:
        JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)
