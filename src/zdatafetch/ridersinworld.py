"""Zwift riders in world data fetching and management.

Provides access to riders currently in a specific world from Zwift's unofficial API.
"""

import json
from typing import Any

import httpx

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zdatafetch.auth import ZwiftAuth
from zdatafetch.config import Config
from zdatafetch.logging_config import get_logger
from zdatafetch.worlds import get_world_id

logger = get_logger(__name__)


class ZwiftRidersInWorld:
  """Zwift riders in world data.

  Represents riders currently active in a specific Zwift world from the
  unofficial API.

  API Endpoint: GET https://us-or-rly101.zwift.com/relay/worlds/{worldId}

  Documentation: https://github.com/strukturunion-mmw/zwift-api-documentation

  Synchronous usage:
      riders = ZwiftRidersInWorld()
      riders.fetch(1)  # Watopia
      print(f"Riders in Watopia: {riders.rider_count()}")

      # Or use world name
      riders.fetch_by_name('watopia')
      print(riders)  # Pretty print all data

  Batch usage:
      riders_data = ZwiftRidersInWorld.fetch_multiple(1, 3, 10)
      for world_id, riders in riders_data.items():
          print(f"World {world_id}: {riders.rider_count()} riders")

  Attributes:
      world_id: World ID for this data
      riders: List of rider objects in the world
  """

  BASE_URL = 'https://us-or-rly101.zwift.com'

  def __init__(self) -> None:
    """Initialize empty riders in world data (no auth parameter).

    Credentials are loaded from Config at fetch time.
    """
    self._raw: str = ''  # Raw JSON response
    self._fetched: dict[str, Any] = {}  # Parsed data
    self.processed: dict = {}  # Reserved for future use

    # Populated after fetch
    self.world_id: int = 0
    self.riders: list[dict[str, Any]] = []

  def fetch(self, world_id: int) -> None:
    """Fetch riders in a specific world.

    Loads credentials from Config, authenticates, fetches data,
    and populates instance attributes.

    Args:
        world_id: Zwift world ID

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

    logger.debug(f'Fetching riders in world {world_id}')

    # Authenticate
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch data
    self.world_id = world_id

    url = f'{self.BASE_URL}/relay/worlds/{world_id}'

    try:
      with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=30.0)

        if response.status_code == 404:
          raise NetworkError(f'World {world_id} not found')
        if response.status_code != 200:
          raise NetworkError(
            f'Failed to fetch riders for world {world_id}: '
            f'HTTP {response.status_code} - {response.text}',
          )

        # Parse and populate attributes
        self._parse_response(response.text)

        # Store raw response as formatted JSON from parsed data
        self._raw = json.dumps(self._fetched, indent=2)
        logger.info(
          f'Successfully fetched {len(self.riders)} riders in world {world_id}',
        )

    except httpx.TimeoutException as e:
      raise NetworkError(
        f'Request timed out fetching riders for world {world_id}: {e}',
      ) from e
    except httpx.HTTPError as e:
      raise NetworkError(
        f'Network error fetching riders for world {world_id}: {e}',
      ) from e

  def fetch_by_name(self, world_name: str) -> None:
    """Fetch riders in a world by world name.

    Convenience method that looks up world ID by name.

    Args:
        world_name: Name of the world (e.g., 'watopia', 'london')

    Raises:
        ValueError: If world name not recognized
        ConfigError: If credentials not configured
        NetworkError: If API request fails
    """
    world_id = get_world_id(world_name)
    if world_id is None:
      raise ValueError(
        f'Unknown world name: {world_name}. '
        f'Valid names: watopia, richmond, london, newyork, innsbruck, bologna, '
        f'yorkshire, critcity, makuri, france, paris, scotland',
      )
    self.fetch(world_id)

  @classmethod
  def fetch_multiple(
    cls,
    *world_ids: int,
  ) -> dict[int, 'ZwiftRidersInWorld']:
    """Fetch multiple worlds' riders, returning dict of objects.

    Args:
        *world_ids: World IDs to fetch

    Returns:
        Dictionary mapping world IDs to ZwiftRidersInWorld objects

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails

    Example:
        riders_data = ZwiftRidersInWorld.fetch_multiple(1, 3, 10)
        for world_id, riders in riders_data.items():
            print(f"World {world_id}: {riders.rider_count()} riders")
    """
    if not world_ids:
      logger.warning('No world IDs provided for batch fetch')
      return {}

    # Load credentials once
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(f'Fetching riders for {len(world_ids)} worlds in batch')

    # Authenticate once
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch all riders
    results = {}
    with httpx.Client() as client:
      for world_id in world_ids:
        try:
          url = f'{cls.BASE_URL}/relay/worlds/{world_id}'
          response = client.get(url, headers=headers, timeout=30.0)

          if response.status_code == 200:
            riders_obj = cls()
            riders_obj.world_id = world_id
            riders_obj._parse_response(response.text)
            riders_obj._raw = json.dumps(riders_obj._fetched, indent=2)
            results[world_id] = riders_obj
            logger.debug(
              f'Successfully fetched {len(riders_obj.riders)} '
              f'riders for world {world_id}',
            )
          else:
            logger.warning(
              f'Failed to fetch riders for world {world_id}: '
              f'HTTP {response.status_code}',
            )

        except Exception as e:
          logger.error(f'Error fetching riders for world {world_id}: {e}')
          continue

    logger.info(
      f'Successfully fetched riders for {len(results)}/{len(world_ids)} worlds in batch',
    )
    return results

  def _parse_response(self, raw_json: str) -> None:
    """Parse raw JSON string into structured riders data.

    Populates instance attributes from parsed data.

    Args:
        raw_json: JSON string from API response
    """
    if not raw_json:
      logger.warning('No data to parse')
      return

    parsed = parse_json_safe(raw_json, context=f'world {self.world_id}')
    if not isinstance(parsed, dict):
      logger.error(
        f'Expected dict for riders in world data, got {type(parsed).__name__}',
      )
      self._fetched = {'riders': []}
      self.riders = []
      return

    # The response is a dict with various fields including rider lists
    # Store the full dict and extract riders if present
    self._fetched = parsed

    # Extract riders - they might be in 'friendsInWorld' or 'playerEntryList' or similar
    # We'll store the full response and let the user navigate it
    if 'friendsInWorld' in parsed:
      self.riders = parsed['friendsInWorld']
    elif 'playerEntryList' in parsed:
      self.riders = parsed['playerEntryList']
    else:
      # Store empty list if no recognized rider field
      self.riders = []

    logger.debug(
      f'Successfully parsed world {self.world_id} data with {len(self.riders)} riders',
    )

  def rider_count(self) -> int:
    """Return count of riders in world.

    Returns:
        Number of riders in the world
    """
    return len(self.riders)

  def rider_ids(self) -> list[int]:
    """Return list of rider IDs in world.

    Returns:
        List of rider IDs
    """
    return [r.get('id', 0) for r in self.riders if 'id' in r]

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
    """Return human-readable string with riders in world data.

    Returns:
        Formatted string showing riders data
    """
    if not self._fetched:
      return 'ZwiftRidersInWorld(no data)'

    # Format all fields for display like profile.py does
    lines = [f'ZwiftRidersInWorld(world_id={self.world_id})']
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
      return 'ZwiftRidersInWorld()'
    return (
      f'ZwiftRidersInWorld(world_id={self.world_id}, riders={len(self.riders)})'
    )

  def asdict(self) -> dict[str, Any]:
    """Return underlying data as dictionary.

    Returns:
        Riders in world data dictionary
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
    """Serialize riders in world data to formatted JSON string.

    Returns:
        JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)
