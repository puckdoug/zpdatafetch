"""Zwift worlds data fetching and management.

Provides access to active worlds from Zwift's unofficial API.
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


# World ID mapping (name -> ID)
# Note: Bologna (6) and Crit City (8) are event-only worlds and may not be
# accessible through the standard relay API endpoints
WORLD_IDS = {
  'watopia': 1,
  'richmond': 2,
  'london': 3,
  'newyork': 4,
  'innsbruck': 5,
  'bologna': 6,  # Event-only, may not be accessible via relay API
  'yorkshire': 7,
  'critcity': 8,  # Event-only, may not be accessible via relay API
  'makuri': 9,
  'makuriislands': 9,  # Alias
  'france': 10,
  'paris': 11,
  'scotland': 13,
}


def get_world_id(world_name: str) -> int | None:
  """Get world ID from world name (case insensitive).

  Args:
      world_name: Name of the world

  Returns:
      World ID or None if not found
  """
  return WORLD_IDS.get(world_name.lower().replace(' ', ''))


def get_world_name(world_id: int) -> str | None:
  """Get world name from world ID.

  Args:
      world_id: ID of the world

  Returns:
      World name or None if not found
  """
  for name, wid in WORLD_IDS.items():
    if wid == world_id and not name.endswith('islands'):  # Skip aliases
      return name.capitalize()
  return None


class ZwiftWorlds:
  """Zwift worlds data.

  Represents active worlds from Zwift's unofficial API.

  API Endpoint: GET https://us-or-rly101.zwift.com/relay/worlds

  Documentation: https://github.com/strukturunion-mmw/zwift-api-documentation

  Synchronous usage:
      worlds = ZwiftWorlds()
      worlds.fetch()
      print(f"Active worlds: {worlds.world_count()}")
      print(worlds)  # Pretty print all data

  Attributes:
      worlds: List of world objects
  """

  BASE_URL = 'https://us-or-rly101.zwift.com'

  def __init__(self) -> None:
    """Initialize empty worlds data (no auth parameter).

    Credentials are loaded from Config at fetch time.
    """
    self._raw: str = ''  # Raw JSON response
    self._fetched: dict[str, Any] = {}  # Parsed data
    self.processed: dict = {}  # Reserved for future use

    # Populated after fetch
    self.worlds: list[dict[str, Any]] = []

  def fetch(self) -> None:
    """Fetch active worlds data.

    Loads credentials from Config, authenticates, fetches data,
    and populates instance attributes.

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

    logger.debug('Fetching active worlds')

    # Authenticate
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch data
    url = f'{self.BASE_URL}/relay/worlds'

    try:
      with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=30.0)

        if response.status_code != 200:
          raise NetworkError(
            f'Failed to fetch worlds: HTTP {response.status_code} - {response.text}',
          )

        # Parse and populate attributes
        self._parse_response(response.text)

        # Store raw response as formatted JSON from parsed data
        self._raw = json.dumps(self._fetched, indent=2)
        logger.info(f'Successfully fetched {len(self.worlds)} active worlds')

    except httpx.TimeoutException as e:
      raise NetworkError(f'Request timed out fetching worlds: {e}') from e
    except httpx.HTTPError as e:
      raise NetworkError(f'Network error fetching worlds: {e}') from e

  def _parse_response(self, raw_json: str) -> None:
    """Parse raw JSON string into structured worlds data.

    Populates instance attributes from parsed data.

    Args:
        raw_json: JSON string from API response
    """
    if not raw_json:
      logger.warning('No data to parse')
      return

    parsed = parse_json_safe(raw_json, context='worlds')

    # Handle both list and dict responses
    if isinstance(parsed, list):
      # Direct list of worlds
      self._fetched = {'worlds': parsed}
      self.worlds = parsed
    elif isinstance(parsed, dict):
      # Dict response - could have 'worlds' key or be a single world object
      if 'worlds' in parsed:
        # Response has a 'worlds' key
        self.worlds = (
          parsed['worlds']
          if isinstance(parsed['worlds'], list)
          else [parsed['worlds']]
        )
        self._fetched = {'worlds': self.worlds}
      else:
        # Single world object - wrap in list
        self.worlds = [parsed]
        self._fetched = {'worlds': self.worlds}
    else:
      logger.error(
        f'Expected list or dict for worlds data, got {type(parsed).__name__}'
      )
      self._fetched = {'worlds': []}
      self.worlds = []
      return

    logger.debug(f'Successfully parsed {len(self.worlds)} worlds')

  def world_count(self) -> int:
    """Return count of active worlds.

    Returns:
        Number of active worlds
    """
    return len(self.worlds)

  def world_ids(self) -> list[int]:
    """Return list of active world IDs.

    Returns:
        List of world IDs
    """
    return [w.get('worldId', 0) for w in self.worlds if 'worldId' in w]

  def world_names(self) -> list[str]:
    """Return list of active world names.

    Returns:
        List of world names
    """
    names = []
    for world_id in self.world_ids():
      name = get_world_name(world_id)
      if name:
        names.append(name)
      else:
        names.append(f'Unknown({world_id})')
    return names

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
    """Return human-readable string with worlds data.

    Returns:
        Formatted string showing worlds data
    """
    if not self._fetched:
      return 'ZwiftWorlds(no data)'

    # Format all fields for display like profile.py does
    lines = ['ZwiftWorlds()']
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
      return 'ZwiftWorlds()'
    return f'ZwiftWorlds(worlds={len(self.worlds)})'

  def asdict(self) -> dict[str, Any]:
    """Return underlying data as dictionary.

    Returns:
        Worlds data dictionary
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
    """Serialize worlds data to formatted JSON string.

    Returns:
        JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)
