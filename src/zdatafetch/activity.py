"""Zwift activity data fetching and management.

Provides access to activity history from Zwift's unofficial API.
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


class ZwiftActivity:
  """Zwift activity data.

  Represents a rider's activity history from Zwift's unofficial API.

  API Endpoint: GET https://us-or-rly101.zwift.com/api/profiles/{riderId}/activities/?start={start}&limit={limit}

  Documentation: https://github.com/strukturunion-mmw/zwift-api-documentation

  Synchronous usage:
      activity = ZwiftActivity()
      activity.fetch(550564)
      print(f"Activities: {activity.activity_count()}")
      print(activity)  # Pretty print all data

  Batch usage:
      activities = ZwiftActivity.fetch_multiple(550564, 123456)
      for rider_id, activity in activities.items():
          print(f"{rider_id}: {activity.activity_count()} activities")

  Attributes:
      rider_id: Rider ID for this data
      start: Starting activity ID (for pagination)
      limit: Number of activities to fetch
      activities: List of activity objects
  """

  BASE_URL = 'https://us-or-rly101.zwift.com'

  def __init__(self) -> None:
    """Initialize empty activity data (no auth parameter).

    Credentials are loaded from Config at fetch time.
    """
    self._raw: str = ''  # Raw JSON response
    self._fetched: dict[str, Any] = {}  # Parsed data
    self.processed: dict = {}  # Reserved for future use

    # Populated after fetch
    self.rider_id: int = 0
    self.start: int = 0
    self.limit: int = 20
    self.activities: list[dict[str, Any]] = []

  def fetch(
    self,
    rider_id: int,
    start: int = 0,
    limit: int = 20,
  ) -> None:
    """Fetch activity data for a single rider.

    Loads credentials from Config, authenticates, fetches data,
    and populates instance attributes.

    Args:
        rider_id: Zwift rider ID
        start: Starting activity ID (default 0)
        limit: Number of activities to fetch (default 20)

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
      f'Fetching activities for rider {rider_id} (start={start}, limit={limit})'
    )

    # Authenticate
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch data
    self.rider_id = rider_id
    self.start = start
    self.limit = limit

    url = f'{self.BASE_URL}/api/profiles/{rider_id}/activities/'
    params = {'start': start, 'limit': limit}

    try:
      with httpx.Client() as client:
        response = client.get(url, headers=headers, params=params, timeout=30.0)

        if response.status_code == 404:
          raise NetworkError(f'Rider {rider_id} not found')
        if response.status_code != 200:
          raise NetworkError(
            f'Failed to fetch activities for rider {rider_id}: '
            f'HTTP {response.status_code} - {response.text}',
          )

        # Parse and populate attributes
        self._parse_response(response.text)

        # Store raw response as formatted JSON from parsed data
        self._raw = json.dumps(self._fetched, indent=2)
        logger.info(
          f'Successfully fetched {len(self.activities)} activities for rider {rider_id}',
        )

    except httpx.TimeoutException as e:
      raise NetworkError(
        f'Request timed out fetching activities for rider {rider_id}: {e}',
      ) from e
    except httpx.HTTPError as e:
      raise NetworkError(
        f'Network error fetching activities for rider {rider_id}: {e}',
      ) from e

  @classmethod
  def fetch_multiple(
    cls,
    *rider_ids: int,
    start: int = 0,
    limit: int = 20,
  ) -> dict[int, 'ZwiftActivity']:
    """Fetch multiple riders' activities, returning dict of objects.

    Args:
        *rider_ids: Zwift rider IDs to fetch
        start: Starting activity ID (default 0)
        limit: Number of activities per rider (default 20)

    Returns:
        Dictionary mapping rider IDs to ZwiftActivity objects

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails

    Example:
        activities = ZwiftActivity.fetch_multiple(550564, 123456, limit=10)
        for rider_id, activity in activities.items():
            print(f"{rider_id}: {activity.activity_count()} activities")
    """
    if not rider_ids:
      logger.warning('No rider IDs provided for batch fetch')
      return {}

    # Load credentials once
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(f'Fetching activities for {len(rider_ids)} riders in batch')

    # Authenticate once
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch all activities
    results = {}
    with httpx.Client() as client:
      for rider_id in rider_ids:
        try:
          url = f'{cls.BASE_URL}/api/profiles/{rider_id}/activities/'
          params = {'start': start, 'limit': limit}
          response = client.get(
            url, headers=headers, params=params, timeout=30.0
          )

          if response.status_code == 200:
            activity_obj = cls()
            activity_obj.rider_id = rider_id
            activity_obj.start = start
            activity_obj.limit = limit
            activity_obj._parse_response(response.text)
            activity_obj._raw = json.dumps(activity_obj._fetched, indent=2)
            results[rider_id] = activity_obj
            logger.debug(
              f'Successfully fetched {len(activity_obj.activities)} '
              f'activities for rider {rider_id}',
            )
          else:
            logger.warning(
              f'Failed to fetch activities for rider {rider_id}: '
              f'HTTP {response.status_code}',
            )

        except Exception as e:
          logger.error(f'Error fetching activities for rider {rider_id}: {e}')
          continue

    logger.info(
      f'Successfully fetched activities for {len(results)}/{len(rider_ids)} riders in batch',
    )
    return results

  def _parse_response(self, raw_json: str) -> None:
    """Parse raw JSON string into structured activity data.

    Populates instance attributes from parsed data.

    Args:
        raw_json: JSON string from API response
    """
    if not raw_json:
      logger.warning('No data to parse')
      return

    parsed = parse_json_safe(raw_json, context='activities')
    if not isinstance(parsed, list):
      logger.error(
        f'Expected list for activities data, got {type(parsed).__name__}'
      )
      self._fetched = {'activities': []}
      self.activities = []
      return

    self._fetched = {'activities': parsed}
    self.activities = parsed

    logger.debug(
      f'Successfully parsed {len(self.activities)} activities for rider {self.rider_id}',
    )

  def activity_count(self) -> int:
    """Return count of activities.

    Returns:
        Number of activities fetched
    """
    return len(self.activities)

  def activity_ids(self) -> list[int]:
    """Return list of activity IDs.

    Returns:
        List of activity IDs
    """
    return [a.get('id', 0) for a in self.activities if 'id' in a]

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
    """Return human-readable string with activity data.

    Returns:
        Formatted string showing activity data
    """
    if not self._fetched:
      return 'ZwiftActivity(no data)'

    # Format all fields for display like profile.py does
    lines = [
      f'ZwiftActivity(rider_id={self.rider_id}, start={self.start}, limit={self.limit})'
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
      return 'ZwiftActivity()'
    return f'ZwiftActivity(rider_id={self.rider_id}, activities={len(self.activities)})'

  def asdict(self) -> dict[str, Any]:
    """Return underlying data as dictionary.

    Returns:
        Activity data dictionary
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
    """Serialize activity data to formatted JSON string.

    Returns:
        JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)
