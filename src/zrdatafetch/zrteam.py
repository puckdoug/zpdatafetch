"""Unified ZRTeam class with both sync and async fetch capabilities.

This module provides the ZRTeam class for fetching and storing team/club
roster data from the Zwiftracing API, including all team member details
and their current ratings.
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
class ZRTeamRider:
  """Individual team member from a Zwiftracing team roster.

  Represents a single team member with their basic info and current ratings.

  Attributes:
    zwift_id: Rider's Zwift ID
    name: Rider's display name
    gender: Rider's gender (M/F)
    height: Height in cm
    weight: Weight in kg
    current_rating: Current category rating
    current_category_mixed: Current mixed category
    current_category_womens: Current women's category (if applicable)
    max30_rating: Max30 rating
    max30_category_mixed: Max30 mixed category
    max30_category_womens: Max30 women's category
    max90_rating: Max90 rating
    max90_category_mixed: Max90 mixed category
    max90_category_womens: Max90 women's category
    power_awc: Anaerobic work capacity (watts)
    power_cp: Critical power (watts)
    power_cs: Compound score
    power_w5: 5-second power (watts)
    power_w15: 15-second power
    power_w30: 30-second power
    power_w60: 60-second power
    power_w120: 2-minute power
    power_w300: 5-minute power
    power_w1200: 20-minute power
    power_wkg5: 5-second power per kg
    power_wkg15: 15-second power per kg
    power_wkg30: 30-second power per kg
    power_wkg60: 60-second power per kg
    power_wkg120: 2-minute power per kg
    power_wkg300: 5-minute power per kg
    power_wkg1200: 20-minute power per kg
  """

  zwift_id: int = 0
  name: str = ''
  gender: str = 'M'
  height: float = 0.0
  weight: float = 0.0
  current_rating: float = 0.0
  current_category_mixed: str = ''
  current_category_womens: str = ''
  max30_rating: float = 0.0
  max30_category_mixed: str = ''
  max30_category_womens: str = ''
  max90_rating: float = 0.0
  max90_category_mixed: str = ''
  max90_category_womens: str = ''
  power_awc: float = 0.0
  power_cp: float = 0.0
  power_cs: float = 0.0
  power_w5: float = 0.0
  power_w15: float = 0.0
  power_w30: float = 0.0
  power_w60: float = 0.0
  power_w120: float = 0.0
  power_w300: float = 0.0
  power_w1200: float = 0.0
  power_wkg5: float = 0.0
  power_wkg15: float = 0.0
  power_wkg30: float = 0.0
  power_wkg60: float = 0.0
  power_wkg120: float = 0.0
  power_wkg300: float = 0.0
  power_wkg1200: float = 0.0

  def to_dict(self) -> dict[str, Any]:
    """Return dictionary representation of team rider.

    Returns:
      Dictionary with all attributes
    """
    return asdict(self)


# ===============================================================================
@dataclass
class ZRTeam(ZR_obj):
  """Team roster data from Zwiftracing API.

  Represents a Zwift team/club with all member information including
  their ratings, power metrics, and category rankings. Supports both
  synchronous and asynchronous operations.

  Synchronous usage:
    team = ZRTeam()
    team.fetch(team_id=456)
    print(team.json())

  Asynchronous usage:
    async with AsyncZR_obj() as zr:
      team = ZRTeam()
      team.set_session(zr)
      await team.afetch(team_id=456)
      print(team.json())

  Attributes:
    team_id: The team/club ID
    team_name: Name of the team/club
    riders: List of ZRTeamRider objects for team members
  """

  # Public attributes (in __init__)
  team_id: int = 0
  team_name: str = ''
  riders: list[ZRTeamRider] = field(default_factory=list)

  # Private attributes (not in __init__)
  _raw: dict = field(default_factory=dict, init=False, repr=False)
  _team: dict = field(default_factory=dict, init=False, repr=False)
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
  def fetch(self, team_id: int | None = None) -> None:
    """Fetch team roster data from the Zwiftracing API (synchronous).

    Fetches all team members and their data for a specific team ID from
    the Zwiftracing API.

    Args:
      team_id: The team ID to fetch (uses self.team_id if not provided)

    Raises:
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      team = ZRTeam()
      team.fetch(team_id=456)
      print(team.json())
    """
    # Use provided value or default
    if team_id is not None:
      self.team_id = team_id

    if self.team_id == 0:
      logger.warning('No team_id provided for fetch')
      return

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(f'Fetching team roster for team_id={self.team_id}')

    # Endpoint is /public/clubs/{team_id}/0 (0 is starting rider offset)
    endpoint = f'/public/clubs/{self.team_id}/0'

    # Fetch JSON from API
    headers = {'Authorization': config.authorization}
    try:
      self._raw = self.fetch_json(endpoint, headers=headers)
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch team roster: {e}')
      raise

    # Parse response
    self._parse_response()

  # -----------------------------------------------------------------------
  async def afetch(self, team_id: int | None = None) -> None:
    """Fetch team roster data from the Zwiftracing API (asynchronous).

    Fetches all team members and their data for a specific team ID from
    the Zwiftracing API.

    Args:
      team_id: The team ID to fetch (uses self.team_id if not provided)

    Raises:
      ZRNetworkError: If the API request fails
      ZRConfigError: If authorization is not configured

    Example:
      team = ZRTeam()
      team.set_session(zr)
      await team.afetch(team_id=456)
      print(team.json())
    """
    # Use provided value or default
    if team_id is not None:
      self.team_id = team_id

    if self.team_id == 0:
      logger.warning('No team_id provided for fetch')
      return

    # Get authorization from config
    config = Config()
    config.load()
    if not config.authorization:
      raise ZRConfigError(
        'Zwiftracing authorization not found. Please run "zrdata config" to set it up.',
      )

    logger.debug(f'Fetching team roster for team_id={self.team_id} (async)')

    # Create temporary session if none provided
    if not self._zr:
      self._zr = AsyncZR_obj()
      await self._zr.init_client()
      owns_session = True
    else:
      owns_session = False

    try:
      # Endpoint is /public/clubs/{team_id}/0 (0 is starting rider offset)
      endpoint = f'/public/clubs/{self.team_id}/0'

      # Fetch JSON from API
      headers = {'Authorization': config.authorization}
      self._raw = await self._zr.fetch_json(endpoint, headers=headers)

      # Parse response
      self._parse_response()
      logger.info(f'Successfully fetched team roster for team_id={self.team_id}')
    except ZRNetworkError as e:
      logger.error(f'Failed to fetch team roster: {e}')
      raise
    finally:
      # Clean up temporary session if we created one
      if owns_session and self._zr:
        await self._zr.close()

  # -----------------------------------------------------------------------
  def _parse_response(self) -> None:
    """Parse API response into team and rider objects.

    Extracts team information and all team member data from the raw API
    response and creates ZRTeamRider objects for each member.
    """
    if not self._raw:
      logger.warning('No data to parse')
      return

    self._team = self._raw

    # Check for error in response
    if isinstance(self._team, dict) and 'message' in self._team:
      logger.error(f"API error: {self._team['message']}")
      return

    # Response should be a dict with team info
    if not isinstance(self._team, dict):
      logger.warning('Expected dict response, got different format')
      return

    try:
      # Extract team name
      self.team_name = self._team.get('name', '')

      # Parse riders list
      riders_list = self._team.get('riders', [])
      if not isinstance(riders_list, list):
        logger.warning('Expected riders to be a list')
        return

      for rider_data in riders_list:
        try:
          # Extract nested structures safely
          race = rider_data.get('race', {})
          current = race.get('current', {})
          max30 = race.get('max30', {})
          max90 = race.get('max90', {})
          power = rider_data.get('power', {})

          # Extract categories
          current_mixed = current.get('mixed', {})
          current_womens = current.get('womens', {})
          max30_mixed = max30.get('mixed', {})
          max30_womens = max30.get('womens', {})
          max90_mixed = max90.get('mixed', {})
          max90_womens = max90.get('womens', {})

          rider = ZRTeamRider(
            zwift_id=rider_data.get('riderId', 0),
            name=rider_data.get('name', ''),
            gender=rider_data.get('gender', 'M'),
            height=float(rider_data.get('height', 0.0)),
            weight=float(rider_data.get('weight', 0.0)),
            current_rating=float(current.get('rating', 0.0)),
            current_category_mixed=current_mixed.get('category', ''),
            current_category_womens=current_womens.get('category', ''),
            max30_rating=float(max30.get('rating', 0.0)),
            max30_category_mixed=max30_mixed.get('category', ''),
            max30_category_womens=max30_womens.get('category', ''),
            max90_rating=float(max90.get('rating', 0.0)),
            max90_category_mixed=max90_mixed.get('category', ''),
            max90_category_womens=max90_womens.get('category', ''),
            power_awc=float(power.get('AWC', 0.0)),
            power_cp=float(power.get('CP', 0.0)),
            power_cs=float(power.get('compoundScore', 0.0)),
            power_w5=float(power.get('w5', 0.0)),
            power_w15=float(power.get('w15', 0.0)),
            power_w30=float(power.get('w30', 0.0)),
            power_w60=float(power.get('w60', 0.0)),
            power_w120=float(power.get('w120', 0.0)),
            power_w300=float(power.get('w300', 0.0)),
            power_w1200=float(power.get('w1200', 0.0)),
            power_wkg5=float(power.get('wkg5', 0.0)),
            power_wkg15=float(power.get('wkg15', 0.0)),
            power_wkg30=float(power.get('wkg30', 0.0)),
            power_wkg60=float(power.get('wkg60', 0.0)),
            power_wkg120=float(power.get('wkg120', 0.0)),
            power_wkg300=float(power.get('wkg300', 0.0)),
            power_wkg1200=float(power.get('wkg1200', 0.0)),
          )
          self.riders.append(rider)
        except (KeyError, TypeError, ValueError) as e:
          logger.warning(f'Skipping malformed rider in team: {e}')
          continue

      logger.debug(
        f'Successfully parsed {len(self.riders)} team members from team_id={self.team_id}',
      )
    except Exception as e:
      logger.error(f'Error parsing response: {e}')

  # -----------------------------------------------------------------------
  def to_dict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with all public attributes and riders as dicts
    """
    return {
      'team_id': self.team_id,
      'team_name': self.team_name,
      'riders': [r.to_dict() for r in self.riders],
    }
