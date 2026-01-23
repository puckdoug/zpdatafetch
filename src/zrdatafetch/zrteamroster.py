"""Pure dataclasses for Zwiftracing team roster data.

This module provides dataclasses for representing team rosters without
any fetch logic. Fetching is handled by ZRTeamFetch.
"""

from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ZRTeamMember:
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
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
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

  # Field classification
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRTeamMember':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing team member data

    Returns:
      ZRTeamMember instance with parsed fields
    """
    known_fields = {
      'riderId',
      'name',
      'gender',
      'height',
      'weight',
      'race',
      'power',
    }

    recognized_but_excluded: set[str] = set()

    try:
      # Extract nested structures safely
      race = data.get('race', {})
      current = race.get('current', {})
      max30 = race.get('max30', {})
      max90 = race.get('max90', {})
      power = data.get('power', {})

      # Extract categories
      current_mixed = current.get('mixed', {})
      current_womens = current.get('womens', {})
      max30_mixed = max30.get('mixed', {})
      max30_womens = max30.get('womens', {})
      max90_mixed = max90.get('mixed', {})
      max90_womens = max90.get('womens', {})

      # Classify remaining fields
      excluded = {}
      extra = {}
      for key, value in data.items():
        if key not in known_fields:
          if key in recognized_but_excluded:
            excluded[key] = value
          else:
            extra[key] = value

      return cls(
        zwift_id=data.get('riderId', 0),
        name=data.get('name', ''),
        gender=data.get('gender', 'M'),
        height=float(data.get('height', 0.0)),
        weight=float(data.get('weight', 0.0)),
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
        _excluded=excluded,
        _extra=extra,
      )
    except (KeyError, TypeError, ValueError) as e:
      logger.warning(f'Error parsing team member data: {e}')
      return cls()

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with all public attributes
    """
    result = asdict(self)
    result.pop('_extra', None)
    result.pop('_excluded', None)
    return result

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)


@dataclass(slots=True)
class ZRTeamRoster(Sequence):
  """Team roster data from Zwiftracing API.

  Represents a Zwift team/club with all member information.
  Implements Sequence protocol for accessing individual team members.

  Attributes:
    team_id: The team/club ID
    team_name: Name of the team/club
    _members: List of ZRTeamMember objects (internal)
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
  """

  # Public metadata fields
  team_id: int = 0
  team_name: str = ''

  # Collection of team members (private)
  _members: list[ZRTeamMember] = field(
    default_factory=list,
    repr=False,
    init=False,
  )

  # Field classification
  _excluded: dict[str, Any] = field(
    default_factory=dict,
    repr=False,
    init=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict,
    repr=False,
    init=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any], team_id: int = 0) -> 'ZRTeamRoster':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing team roster data
      team_id: Team ID (injected if not in response)

    Returns:
      ZRTeamRoster instance with parsed fields and members
    """
    known_fields = {
      'name',
      'riders',
      'teamId',
      'clubId',
    }

    recognized_but_excluded: set[str] = set()

    # Parse team members
    riders_list = data.get('riders', [])
    members = []
    for rider_data in riders_list:
      try:
        members.append(ZRTeamMember.from_dict(rider_data))
      except (KeyError, TypeError, ValueError) as e:
        logger.warning(f'Skipping malformed rider in team: {e}')
        continue

    # Classify remaining fields
    excluded = {}
    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        if key in recognized_but_excluded:
          excluded[key] = value
        else:
          extra[key] = value

    # Create instance
    instance = cls(
      team_id=data.get('teamId', data.get('clubId', team_id)),
      team_name=str(data.get('name', '')),
    )

    # Set internal fields
    instance._members = members
    instance._excluded = excluded
    instance._extra = extra

    return instance

  # Sequence protocol implementation
  def __len__(self) -> int:
    """Return the number of team members.

    Returns:
      Number of members
    """
    return len(self._members)

  def __getitem__(self, index: int) -> ZRTeamMember:  # type: ignore[override]
    """Access team member by index.

    Args:
      index: Integer index

    Returns:
      ZRTeamMember object

    Raises:
      IndexError: If index out of range
    """
    return self._members[index]

  def __iter__(self) -> Iterator[ZRTeamMember]:
    """Iterate over team members.

    Returns:
      Iterator over ZRTeamMember objects
    """
    return iter(self._members)

  def __repr__(self) -> str:
    """Return detailed representation.

    Returns:
      String showing team info and member count
    """
    return (
      f'ZRTeamRoster(team_id={self.team_id}, team_name={self.team_name!r}, '
      f'members={len(self._members)})'
    )

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with team metadata and members
    """
    return {
      'team_id': self.team_id,
      'team_name': self.team_name,
      'riders': [m.asdict() for m in self._members],
    }

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)
