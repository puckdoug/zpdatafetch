"""Pure dataclasses for Zwiftracing team roster data.

This module provides dataclasses for representing team rosters without
any fetch logic. Fetching is handled by ZRTeamFetch.
"""

from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr_utils import (
  extract_nested_value,
  safe_float,
  safe_int,
  safe_str,
)

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
      # Extract using safe utilities
      zwift_id = safe_int(data.get('riderId'))
      name = safe_str(data.get('name'))
      gender = safe_str(data.get('gender'), default='M')
      height = safe_float(data.get('height'))
      weight = safe_float(data.get('weight'))

      # Current ratings and categories
      current_rating = safe_float(
        extract_nested_value(data, 'race', 'current', 'rating'),
      )
      current_category_mixed = safe_str(
        extract_nested_value(data, 'race', 'current', 'mixed', 'category'),
      )
      current_category_womens = safe_str(
        extract_nested_value(data, 'race', 'current', 'womens', 'category'),
      )

      # Max30 ratings and categories
      max30_rating = safe_float(
        extract_nested_value(data, 'race', 'max30', 'rating')
      )
      max30_category_mixed = safe_str(
        extract_nested_value(data, 'race', 'max30', 'mixed', 'category'),
      )
      max30_category_womens = safe_str(
        extract_nested_value(data, 'race', 'max30', 'womens', 'category'),
      )

      # Max90 ratings and categories
      max90_rating = safe_float(
        extract_nested_value(data, 'race', 'max90', 'rating')
      )
      max90_category_mixed = safe_str(
        extract_nested_value(data, 'race', 'max90', 'mixed', 'category'),
      )
      max90_category_womens = safe_str(
        extract_nested_value(data, 'race', 'max90', 'womens', 'category'),
      )

      # Power metrics
      power_awc = safe_float(extract_nested_value(data, 'power', 'AWC'))
      power_cp = safe_float(extract_nested_value(data, 'power', 'CP'))
      power_cs = safe_float(
        extract_nested_value(data, 'power', 'compoundScore')
      )
      power_w5 = safe_float(extract_nested_value(data, 'power', 'w5'))
      power_w15 = safe_float(extract_nested_value(data, 'power', 'w15'))
      power_w30 = safe_float(extract_nested_value(data, 'power', 'w30'))
      power_w60 = safe_float(extract_nested_value(data, 'power', 'w60'))
      power_w120 = safe_float(extract_nested_value(data, 'power', 'w120'))
      power_w300 = safe_float(extract_nested_value(data, 'power', 'w300'))
      power_w1200 = safe_float(extract_nested_value(data, 'power', 'w1200'))
      power_wkg5 = safe_float(extract_nested_value(data, 'power', 'wkg5'))
      power_wkg15 = safe_float(extract_nested_value(data, 'power', 'wkg15'))
      power_wkg30 = safe_float(extract_nested_value(data, 'power', 'wkg30'))
      power_wkg60 = safe_float(extract_nested_value(data, 'power', 'wkg60'))
      power_wkg120 = safe_float(extract_nested_value(data, 'power', 'wkg120'))
      power_wkg300 = safe_float(extract_nested_value(data, 'power', 'wkg300'))
      power_wkg1200 = safe_float(extract_nested_value(data, 'power', 'wkg1200'))

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
        zwift_id=zwift_id,
        name=name,
        gender=gender,
        height=height,
        weight=weight,
        current_rating=current_rating,
        current_category_mixed=current_category_mixed,
        current_category_womens=current_category_womens,
        max30_rating=max30_rating,
        max30_category_mixed=max30_category_mixed,
        max30_category_womens=max30_category_womens,
        max90_rating=max90_rating,
        max90_category_mixed=max90_category_mixed,
        max90_category_womens=max90_category_womens,
        power_awc=power_awc,
        power_cp=power_cp,
        power_cs=power_cs,
        power_w5=power_w5,
        power_w15=power_w15,
        power_w30=power_w30,
        power_w60=power_w60,
        power_w120=power_w120,
        power_w300=power_w300,
        power_w1200=power_w1200,
        power_wkg5=power_wkg5,
        power_wkg15=power_wkg15,
        power_wkg30=power_wkg30,
        power_wkg60=power_wkg60,
        power_wkg120=power_wkg120,
        power_wkg300=power_wkg300,
        power_wkg1200=power_wkg1200,
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

    # Create instance using safe utilities
    instance = cls(
      team_id=safe_int(data.get('teamId', data.get('clubId', team_id))),
      team_name=safe_str(data.get('name')),
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
