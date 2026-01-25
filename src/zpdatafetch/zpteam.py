"""Python object representations for ZwiftPower team data.

This module defines typed Python objects for team roster data from ZwiftPower's
team API endpoint. Provides both collection and individual team member classes
with explicit typed fields and backwards compatibility.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from zpdatafetch.zp_utils import (
  convert_gender,
  extract_value,
  format_time_hms,
  set_rider_category,
)


@dataclass(slots=True)
class ZPTeamMember:
  """Represents a single team member in a team roster.

  Stores team member data with explicit typed fields and captures
  unknown fields for forward compatibility.

  Attributes:
    Rider identification:
      zwift_id: Rider's Zwift ID
      name: Rider's name
      age: Age category
      flag: Country flag code

    Physical attributes:
      weight: Weight in kg
      height: Height in cm (stored as [value, flag] array)

    Performance metrics:
      ftp: Functional Threshold Power (stored as [value, flag] array)
      zftp: FTP value extracted
      rank: Overall ranking
      skill: Skill rating
      skill_race: Race skill rating
      skill_seg: Segment skill rating
      skill_power: Power skill rating

    Activity stats:
      distance: Total distance ridden (meters)
      climbed: Total elevation climbed (meters)
      energy: Total energy (kJ)
      time: Total riding time (seconds)
      time_hms: Total riding time formatted as hh:mm:ss.sss

    Critical power:
      h_15_watts: 15 second power
      h_15_wkg: 15 second watts/kg
      h_1200_watts: 20 minute power
      h_1200_wkg: 20 minute watts/kg

    Status:
      div: Category (0/10/20/30/40)
      divw: Women's category
      status: Status flag
      zada: Zwift academy flag
  """

  # Rider identification
  zwift_id: int = 0
  name: str = ''
  age: str = ''
  gender: str = ''  # Gender (male/female)
  flag: str = ''

  # Physical attributes
  weight: float = 0.0

  # Performance metrics
  zftp: int = 0
  rank: str = ''
  skill: int = 0
  skill_race: int = 0
  skill_seg: int = 0
  skill_power: int = 0

  # Activity stats
  distance: int = 0
  climbed: int = 0
  energy: int = 0
  time: int = 0
  time_hms: str = ''

  # Critical power
  h_15_watts: str = ''
  h_15_wkg: str = ''
  h_1200_watts: str = ''
  h_1200_wkg: str = ''

  # Status and category
  category: str = ''  # Men's category (A/B/C/D) converted from div
  category_women: str = ''  # Women's category (A/B/C/D) converted from divw
  status: str = ''
  zada: bool = False
  reg: int = 0

  # Field classification dicts
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPTeamMember':
    """Create instance from API response dict.

    Known fields are extracted with type coercion and transformations.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing team member data from API response

    Returns:
      ZPTeamMember instance with parsed fields
    """
    known_fields = {
      'zwid',
      'name',
      'age',
      'gender',
      'flag',
      'w',
      'ftp',
      'rank',
      'skill',
      'skill_race',
      'skill_seg',
      'skill_power',
      'distance',
      'climbed',
      'energy',
      'time',
      'h_15_watts',
      'h_15_wkg',
      'h_1200_watts',
      'h_1200_wkg',
      'div',
      'divw',
      'status',
      'zada',
      'reg',
      'aid',
      'r',
      'email',
    }

    # Fields to exclude (recognized from API but not explicitly handled)
    recognized_but_excluded = {
      'aid',
      'r',
      'email',
    }

    # Extract known fields with proper type conversions
    zwift_id = int(data.get('zwid', 0))
    name = str(data.get('name', ''))
    age = str(data.get('age', ''))
    gender = convert_gender(data.get('gender', ''))
    flag = str(data.get('flag', ''))

    # Weight from array format or direct value (using extract_value utility)
    weight_val = extract_value(data.get('w', 0), 0)
    weight = float(weight_val) if weight_val else 0.0

    # FTP from array format or direct value (using extract_value utility)
    ftp_val = extract_value(data.get('ftp', 0), 0)
    try:
      zftp = int(ftp_val) if ftp_val else 0
    except (ValueError, TypeError):
      zftp = 0

    # Performance metrics
    rank = str(data.get('rank', ''))
    skill = int(data.get('skill', 0))
    skill_race = int(data.get('skill_race', 0))
    skill_seg = int(data.get('skill_seg', 0))
    skill_power = int(data.get('skill_power', 0))

    # Activity stats
    distance = int(data.get('distance', 0))
    climbed = int(data.get('climbed', 0))
    energy = int(data.get('energy', 0))
    time = int(data.get('time', 0))
    time_hms = format_time_hms(time)

    # Critical power
    h_15_watts = str(data.get('h_15_watts', ''))
    h_15_wkg = str(data.get('h_15_wkg', ''))
    h_1200_watts = str(data.get('h_1200_watts', ''))
    h_1200_wkg = str(data.get('h_1200_wkg', ''))

    # Status and category
    div = int(data.get('div', 0))
    divw = int(data.get('divw', 0))
    category = set_rider_category(div)
    category_women = set_rider_category(divw)
    status = str(data.get('status', ''))
    zada = int(data.get('zada', 0)) == 1
    reg = int(data.get('reg', 0))

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
      age=age,
      gender=gender,
      flag=flag,
      weight=weight,
      zftp=zftp,
      rank=rank,
      skill=skill,
      skill_race=skill_race,
      skill_seg=skill_seg,
      skill_power=skill_power,
      distance=distance,
      climbed=climbed,
      energy=energy,
      time=time,
      time_hms=time_hms,
      h_15_watts=h_15_watts,
      h_15_wkg=h_15_wkg,
      h_1200_watts=h_1200_watts,
      h_1200_wkg=h_1200_wkg,
      category=category,
      category_women=category_women,
      status=status,
      zada=zada,
      reg=reg,
      _excluded=excluded,
      _extra=extra,
    )

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to team member data for backwards compatibility."""
    if hasattr(self, key):
      return getattr(self, key)
    if key in self._excluded:
      return self._excluded[key]
    if key in self._extra:
      return self._extra[key]
    raise KeyError(key)

  def __contains__(self, key: str) -> bool:
    """Check if a key exists in the team member data."""
    return hasattr(self, key) or key in self._excluded or key in self._extra

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields (candidates for future promotion)."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields (likely from recent API changes)."""
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return the team member data as a dictionary.

    Returns typed field values directly, excluding internal fields.
    """
    return {
      'zwift_id': self.zwift_id,
      'name': self.name,
      'age': self.age,
      'gender': self.gender,
      'flag': self.flag,
      'weight': self.weight,
      'zftp': self.zftp,
      'rank': self.rank,
      'skill': self.skill,
      'skill_race': self.skill_race,
      'skill_seg': self.skill_seg,
      'skill_power': self.skill_power,
      'distance': self.distance,
      'climbed': self.climbed,
      'energy': self.energy,
      'time': self.time,
      'time_hms': self.time_hms,
      'h_15_watts': self.h_15_watts,
      'h_15_wkg': self.h_15_wkg,
      'h_1200_watts': self.h_1200_watts,
      'h_1200_wkg': self.h_1200_wkg,
      'category': self.category,
      'category_women': self.category_women,
      'status': self.status,
      'zada': self.zada,
      'reg': self.reg,
    }

  def json(self) -> str:
    """Return JSON representation of team member data."""
    return json.dumps(self.asdict(), indent=2)


@dataclass(slots=True)
class ZPTeam:
  """Collection of team members for a team roster.

  Stores team-level data and a list of individual team members.
  Provides convenient iteration and indexing operations.

  Attributes:
    _members: List of ZPTeamMember objects
  """

  # Collection of team members
  _members: list[ZPTeamMember] = field(default_factory=list, repr=False)

  # Field classification dicts
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  # Original data dict for backwards compatibility
  _data: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPTeam':
    """Create instance from API response dict.

    Parses team-level fields and creates ZPTeamMember objects
    from the nested 'data' array.

    Args:
      data: Dictionary containing team data from API response

    Returns:
      ZPTeam instance with parsed fields
    """
    known_fields = {'data'}
    recognized_but_excluded: set[str] = set()

    # Parse member list from nested "data" key
    members = []
    for member_data in data.get('data', []):
      members.append(ZPTeamMember.from_dict(member_data))

    # Classify team-level fields
    excluded = {}
    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        if key in recognized_but_excluded:
          excluded[key] = value
        else:
          extra[key] = value

    return cls(
      _members=members,
      _excluded=excluded,
      _extra=extra,
      _data=data,  # Keep original for backwards compatibility
    )

  def __len__(self) -> int:
    """Return the number of team members."""
    return len(self._members)

  def __getitem__(
    self, index: int | slice
  ) -> 'ZPTeamMember | list[ZPTeamMember]':
    """Access team members by index or slice."""
    return self._members[index]

  def __iter__(self):
    """Iterate over team members."""
    return iter(self._members)

  def __repr__(self) -> str:
    """Return detailed representation."""
    return f'ZPTeam(members={len(self._members)})'

  def __str__(self) -> str:
    """Return human-readable string."""
    return f'ZPTeam with {len(self._members)} members'

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields at team level."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields at team level."""
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return team data as a dictionary with typed field values."""
    return {
      'data': [member.asdict() for member in self._members],
    }

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of team members as dictionaries."""
    return [member.asdict() for member in self._members]

  def json(self) -> str:
    """Return JSON representation of team data."""
    return json.dumps(self._data, indent=2)
