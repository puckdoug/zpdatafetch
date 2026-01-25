"""Zwift follower and followee data fetching and management.

Provides access to follower/followee relationship data from Zwift's unofficial API.
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


class ZwiftFollowers:
  """Zwift follower and followee data.

  Represents follower/followee relationships for a rider from Zwift's
  unofficial API.

  API Endpoints:
      GET https://us-or-rly101.zwift.com/api/profiles/{riderId}/followers
      GET https://us-or-rly101.zwift.com/api/profiles/{riderId}/followees

  Documentation: https://github.com/strukturunion-mmw/zwift-api-documentation

  Synchronous usage:
      followers = ZwiftFollowers()
      followers.fetch(550564)
      print(f"Followers: {followers.follower_count()}")
      print(f"Following: {followers.followee_count()}")
      print(followers)  # Pretty print all data

  Batch usage:
      followers_data = ZwiftFollowers.fetch_multiple(550564, 123456)
      for rider_id, data in followers_data.items():
          print(f"Rider {rider_id}: {data.follower_count()} followers")

  Attributes:
      rider_id: Rider ID for this data
      followers: List of follower objects
      followees: List of followee objects
  """

  BASE_URL = 'https://us-or-rly101.zwift.com'

  def __init__(self) -> None:
    """Initialize empty followers data (no auth parameter).

    Credentials are loaded from Config at fetch time.
    """
    self._raw: str = ''  # Raw JSON response
    self._fetched: dict[str, Any] = {}  # Parsed data
    self.processed: dict = {}  # Reserved for future use

    # Populated after fetch
    self.rider_id: int = 0
    self.followers: list[dict[str, Any]] = []
    self.followees: list[dict[str, Any]] = []

  def fetch(
    self,
    rider_id: int,
    include_followers: bool = True,
    include_followees: bool = True,
  ) -> None:
    """Fetch follower/followee data for a single rider.

    Loads credentials from Config, authenticates, fetches data,
    and populates instance attributes.

    Args:
        rider_id: Zwift rider ID
        include_followers: Whether to fetch followers list
        include_followees: Whether to fetch followees list

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails
        AuthenticationError: If authentication fails
    """
    if not include_followers and not include_followees:
      logger.warning(
        'Neither followers nor followees requested, nothing to fetch'
      )
      return

    # Load credentials from config
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(f'Fetching follower data for rider {rider_id}')

    # Authenticate
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch data
    self.rider_id = rider_id
    raw_data = {}

    try:
      with httpx.Client() as client:
        # Fetch followers
        if include_followers:
          url = f'{self.BASE_URL}/api/profiles/{rider_id}/followers'
          response = client.get(url, headers=headers, timeout=30.0)

          if response.status_code == 404:
            raise NetworkError(f'Rider {rider_id} not found')
          if response.status_code != 200:
            raise NetworkError(
              f'Failed to fetch followers for rider {rider_id}: '
              f'HTTP {response.status_code} - {response.text}',
            )

          raw_data['followers'] = response.text
          logger.debug(f'Successfully fetched followers for rider {rider_id}')

        # Fetch followees
        if include_followees:
          url = f'{self.BASE_URL}/api/profiles/{rider_id}/followees'
          response = client.get(url, headers=headers, timeout=30.0)

          if response.status_code == 404:
            raise NetworkError(f'Rider {rider_id} not found')
          if response.status_code != 200:
            logger.warning(
              f'Failed to fetch followees for rider {rider_id}: '
              f'HTTP {response.status_code}',
            )
            # Continue with just followers data
            raw_data['followees'] = '[]'
          else:
            raw_data['followees'] = response.text
            logger.debug(f'Successfully fetched followees for rider {rider_id}')

        # Parse and populate attributes
        self._parse_response(raw_data)

        # Store raw response as formatted JSON from parsed data
        self._raw = json.dumps(self._fetched, indent=2)
        logger.info(f'Successfully fetched follower data for rider {rider_id}')

    except httpx.TimeoutException as e:
      raise NetworkError(
        f'Request timed out fetching follower data for rider {rider_id}: {e}',
      ) from e
    except httpx.HTTPError as e:
      raise NetworkError(
        f'Network error fetching follower data for rider {rider_id}: {e}',
      ) from e

  @classmethod
  def fetch_multiple(
    cls,
    *rider_ids: int,
    include_followers: bool = True,
    include_followees: bool = True,
  ) -> dict[int, 'ZwiftFollowers']:
    """Fetch multiple riders' follower data, returning dict of objects.

    Args:
        *rider_ids: Zwift rider IDs to fetch
        include_followers: Whether to fetch followers lists
        include_followees: Whether to fetch followees lists

    Returns:
        Dictionary mapping rider IDs to ZwiftFollowers objects

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails

    Example:
        followers_data = ZwiftFollowers.fetch_multiple(550564, 123456)
        for rider_id, data in followers_data.items():
            print(f"{rider_id}: {data.follower_count()} followers")
    """
    if not rider_ids:
      logger.warning('No rider IDs provided for batch fetch')
      return {}

    if not include_followers and not include_followees:
      logger.warning(
        'Neither followers nor followees requested, nothing to fetch'
      )
      return {}

    # Load credentials once
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(f'Fetching follower data for {len(rider_ids)} riders in batch')

    # Authenticate once
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch all follower data
    results = {}
    with httpx.Client() as client:
      for rider_id in rider_ids:
        try:
          raw_data = {}

          # Fetch followers
          if include_followers:
            url = f'{cls.BASE_URL}/api/profiles/{rider_id}/followers'
            response = client.get(url, headers=headers, timeout=30.0)

            if response.status_code == 200:
              raw_data['followers'] = response.text
            else:
              logger.warning(
                f'Failed to fetch followers for rider {rider_id}: '
                f'HTTP {response.status_code}',
              )
              continue

          # Fetch followees
          if include_followees:
            url = f'{cls.BASE_URL}/api/profiles/{rider_id}/followees'
            response = client.get(url, headers=headers, timeout=30.0)

            if response.status_code == 200:
              raw_data['followees'] = response.text
            else:
              logger.warning(
                f'Failed to fetch followees for rider {rider_id}: '
                f'HTTP {response.status_code}',
              )
              raw_data['followees'] = '[]'

          # Create object and populate
          followers_obj = cls()
          followers_obj.rider_id = rider_id
          followers_obj._parse_response(raw_data)
          followers_obj._raw = json.dumps(followers_obj._fetched, indent=2)
          results[rider_id] = followers_obj

          logger.debug(
            f'Successfully fetched follower data for rider {rider_id}'
          )

        except Exception as e:
          logger.error(
            f'Error fetching follower data for rider {rider_id}: {e}'
          )
          continue

    logger.info(
      f'Successfully fetched {len(results)}/{len(rider_ids)} follower data in batch',
    )
    return results

  def _parse_response(self, raw_data: dict[str, str]) -> None:
    """Parse raw JSON strings into structured follower data.

    Populates instance attributes from parsed data.

    Args:
        raw_data: Dictionary with 'followers' and/or 'followees' JSON strings
    """
    if not raw_data:
      logger.warning('No data to parse')
      return

    parsed = {}

    # Parse followers
    if 'followers' in raw_data:
      followers_list = parse_json_safe(
        raw_data['followers'], context='followers'
      )
      if isinstance(followers_list, list):
        parsed['followers'] = followers_list
        self.followers = followers_list
      else:
        logger.error(
          f'Expected list for followers, got {type(followers_list).__name__}',
        )
        parsed['followers'] = []
        self.followers = []
    else:
      parsed['followers'] = []
      self.followers = []

    # Parse followees
    if 'followees' in raw_data:
      followees_list = parse_json_safe(
        raw_data['followees'], context='followees'
      )
      if isinstance(followees_list, list):
        parsed['followees'] = followees_list
        self.followees = followees_list
      else:
        logger.error(
          f'Expected list for followees, got {type(followees_list).__name__}',
        )
        parsed['followees'] = []
        self.followees = []
    else:
      parsed['followees'] = []
      self.followees = []

    self._fetched = parsed
    logger.debug(
      f'Successfully parsed {len(self.followers)} followers and '
      f'{len(self.followees)} followees for rider {self.rider_id}',
    )

  def follower_count(self) -> int:
    """Return count of followers.

    Returns:
        Number of followers
    """
    return len(self.followers)

  def followee_count(self) -> int:
    """Return count of followees.

    Returns:
        Number of followees (people this rider follows)
    """
    return len(self.followees)

  def follower_ids(self) -> list[int]:
    """Return list of follower IDs.

    Returns:
        List of rider IDs who follow this rider
    """
    return [f.get('id', 0) for f in self.followers if 'id' in f]

  def followee_ids(self) -> list[int]:
    """Return list of followee IDs.

    Returns:
        List of rider IDs this rider follows
    """
    return [f.get('id', 0) for f in self.followees if 'id' in f]

  def mutual_followers(self) -> list[dict[str, Any]]:
    """Return followers who are also followees (mutual follows).

    Returns:
        List of rider objects who both follow and are followed by this rider
    """
    followee_id_set = set(self.followee_ids())
    return [f for f in self.followers if f.get('id') in followee_id_set]

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
    """Return human-readable string with follower data.

    Returns:
        Formatted string showing follower/followee data
    """
    if not self._fetched:
      return 'ZwiftFollowers(no data)'

    # Format all fields for display like profile.py does
    lines = [f'ZwiftFollowers(rider_id={self.rider_id})']
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
      return 'ZwiftFollowers()'
    return (
      f'ZwiftFollowers(rider_id={self.rider_id}, '
      f'followers={len(self.followers)}, '
      f'followees={len(self.followees)})'
    )

  def asdict(self) -> dict[str, Any]:
    """Return underlying data as dictionary.

    Returns:
        Follower data dictionary
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
    """Serialize follower data to formatted JSON string.

    Returns:
        JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)
