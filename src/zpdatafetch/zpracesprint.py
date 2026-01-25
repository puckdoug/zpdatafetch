"""Python object representations for ZwiftPower race sprint data.

This module defines typed Python objects for race sprint data from ZwiftPower's
event_sprints API endpoint. Provides both collection and individual sprint
result classes with explicit typed fields and backwards compatibility.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from zpdatafetch.zp_utils import (
  convert_gender,
  convert_label_to_pen,
  extract_value,
)


@dataclass(slots=True)
class ZPRiderSprint:
  """Represents a single rider's sprint result in a race.

  Stores rider sprint result data with explicit typed fields and captures
  unknown fields for forward compatibility.

  Attributes:
    Rider identification:
      zwift_id: Rider's Zwift ID
      name: Rider's name
      age: Age category or age string
      gender: Gender (male/female/empty)
      flag: Country flag code
      height: Height in cm
      weight: Weight in kg

    Registration and status:
      category: Category (A/B/C/D or empty)
      pen: Race-specific pen/category letter
      reg: Registration status (1=registered)
      hrm: Heart rate monitor flag
      power_type: Power data type indicator

    Race-specific fields:
      position: Position/rank in sprint
      position_in_cat: Position within category
      display_pos: Display position
      res_id: Result ID
      ftp: Functional Threshold Power
      zada: Zwift Academy status (boolean)
      upg: Upgrade flag
      is_guess: Data guess flag

    Team information:
      team_id: Team ID
      team_name: Team name

    Sprint performance:
      msec: Dict of sprint times by segment (e.g., {'34': 45.397, '35': 671.562})
      watts: Dict of wattage by segment (e.g., {'34': '181', '35': '209'})
      wkg: Dict of watts/kg by segment (e.g., {'34': '2.4', '35': '2.8'})
      s34, s35: Sprint segment numbers
  """

  # Rider identification
  zwift_id: int = 0
  name: str = ''
  age: str = ''
  gender: str = ''
  flag: str = ''
  height: int = 0
  weight: float = 0.0

  # Registration and status
  category: str = ''
  pen: str = ''
  reg: int = 0
  hrm: bool = False
  power_type: int = 0

  # Race-specific fields
  position: int = 0
  position_in_cat: int = 0
  display_pos: int = 0
  res_id: str = ''
  zftp: int = 0
  zada: bool = False
  upg: bool = False
  is_guess: bool = False

  # Team information
  team_id: int | None = None
  team_name: str | None = None

  # Sprint performance data - combined into list format
  sprints: list[dict[str, Any]] = field(default_factory=list)

  # Field classification dicts
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPRiderSprint':
    """Create instance from API response dict.

    Known fields are extracted with type coercion and transformations.
    Field aliases are checked for backwards compatibility.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing rider sprint data from API response

    Returns:
      ZPRiderSprint instance with parsed fields
    """
    known_fields = {
      'zwid',
      'name',
      'age',
      'male',
      'flag',
      'height',
      'weight',
      'category',
      'label',
      'reg',
      'hrm',
      'power_type',
      'pos',
      'position_in_cat',
      'display_pos',
      'res_id',
      'ftp',
      'zada',
      'upg',
      'is_guess',
      'tid',
      'tname',
      'msec',
      'watts',
      'wkg',
      's34',
      's35',
      'note',
      'penalty',
    }

    # Fields to exclude (recognized from API but not explicitly handled)
    recognized_but_excluded = {
      'DT_RowId',
      'pt',
      'topen',
      'tbc',
      'tbd',
      'tc',
      'fl',
      'zid',
    }

    # Extract known fields with proper type conversions
    zwift_id = int(data.get('zwid', 0))
    name = str(data.get('name', ''))
    age = str(data.get('age', ''))

    # Gender conversion (1=male, 0=female)
    gender = convert_gender(int(data.get('male', 0)))

    flag = str(data.get('flag', ''))

    # Height and weight from array format or direct value (using extract_value utility)
    height_val = extract_value(data.get('height', 0), 0)
    height = int(height_val) if height_val else 0

    weight_val = extract_value(data.get('weight', 0), 0)
    weight = float(weight_val) if weight_val else 0.0

    # Category
    category = str(data.get('category', ''))

    # Pen (race-specific category)
    pen = convert_label_to_pen(int(data.get('label', 0)))

    # Registration and status
    reg = int(data.get('reg', 0))
    hrm = int(data.get('hrm', 0)) == 1
    power_type = int(data.get('power_type', 0))

    # Race-specific fields
    position = int(data.get('pos', 0))
    position_in_cat = int(data.get('position_in_cat', 0))
    display_pos = int(data.get('display_pos', 0))
    res_id = str(data.get('res_id', ''))
    zftp_raw = data.get('ftp', 0)
    try:
      zftp = int(zftp_raw) if zftp_raw else 0
    except (ValueError, TypeError):
      zftp = 0
    zada = int(data.get('zada', 0)) == 1
    upg = int(data.get('upg', 0)) == 1
    is_guess = int(data.get('is_guess', 0)) == 1

    # Team information - team_id as int or None
    team_id_raw = data.get('tid')
    team_id: int | None = None
    if team_id_raw is not None and team_id_raw != '':
      try:
        team_id = int(team_id_raw)
        if team_id == 0:
          team_id = None
      except (ValueError, TypeError):
        team_id = None
    team_name_raw = data.get('tname', '')
    team_name: str | None = str(team_name_raw) if team_name_raw else None

    # Build sprints list by combining msec, watts, wkg data
    msec_dict = dict(data.get('msec', {}))
    watts_dict = dict(data.get('watts', {}))
    wkg_dict = dict(data.get('wkg', {}))

    sprints_list = []
    # Use msec keys as the source of truth for sprint IDs
    for sprint_id in msec_dict:
      sprint_entry = {
        'name': sprint_id,  # Will be replaced with actual name by enrichment
        'msec': msec_dict.get(sprint_id),
        'watts': watts_dict.get(sprint_id),
        'wkg': wkg_dict.get(sprint_id),
      }
      sprints_list.append(sprint_entry)

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
      height=height,
      weight=weight,
      category=category,
      pen=pen,
      reg=reg,
      hrm=hrm,
      power_type=power_type,
      position=position,
      position_in_cat=position_in_cat,
      display_pos=display_pos,
      res_id=res_id,
      zftp=zftp,
      zada=zada,
      upg=upg,
      is_guess=is_guess,
      team_id=team_id,
      team_name=team_name,
      sprints=sprints_list,
      _excluded=excluded,
      _extra=extra,
    )

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to sprint data for backwards compatibility."""
    if hasattr(self, key):
      return getattr(self, key)
    if key in self._excluded:
      return self._excluded[key]
    if key in self._extra:
      return self._extra[key]
    raise KeyError(key)

  def __contains__(self, key: str) -> bool:
    """Check if a key exists in the sprint data."""
    return hasattr(self, key) or key in self._excluded or key in self._extra

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields (candidates for future promotion)."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields (likely from recent API changes)."""
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return the sprint data as a dictionary.

    Returns typed field values directly, excluding internal fields.
    """
    return {
      'zwift_id': self.zwift_id,
      'name': self.name,
      'age': self.age,
      'gender': self.gender,
      'flag': self.flag,
      'height': self.height,
      'weight': self.weight,
      'category': self.category,
      'pen': self.pen,
      'reg': self.reg,
      'hrm': self.hrm,
      'power_type': self.power_type,
      'position': self.position,
      'position_in_cat': self.position_in_cat,
      'display_pos': self.display_pos,
      'res_id': self.res_id,
      'zftp': self.zftp,
      'zada': self.zada,
      'upg': self.upg,
      'is_guess': self.is_guess,
      'team_id': self.team_id,
      'team_name': self.team_name,
      'sprints': self.sprints,
    }

  def json(self) -> str:
    """Return JSON representation of sprint data."""
    return json.dumps(self.asdict(), indent=2)


@dataclass(slots=True)
class ZPRaceSprint:
  """Collection of rider sprint results for a race.

  Stores race-level sprint metadata and a list of individual rider sprints.
  Provides convenient iteration and indexing operations.

  Attributes:
    race_id: The race ID
    And other race-level fields
  """

  # Race-level metadata fields
  race_id: int = 0

  # Collection of rider sprints
  _riders: list[ZPRiderSprint] = field(default_factory=list, repr=False)

  # Field classification dicts
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  # Original data dict for backwards compatibility
  _data: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPRaceSprint':
    """Create instance from API response dict.

    Parses race-level fields and creates ZPRiderSprint objects
    from the nested 'data' array.

    Args:
      data: Dictionary containing race sprint data from API response

    Returns:
      ZPRaceSprint instance with parsed fields
    """
    known_fields = {'data', 'race_id'}
    recognized_but_excluded = {'status', 'message', 'event_name'}

    # Parse rider list from nested "data" key
    riders = []
    for rider_data in data.get('data', []):
      riders.append(ZPRiderSprint.from_dict(rider_data))

    # Classify race-level fields
    excluded = {}
    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        if key in recognized_but_excluded:
          excluded[key] = value
        else:
          extra[key] = value

    return cls(
      race_id=int(data.get('race_id', 0)),
      _riders=riders,
      _excluded=excluded,
      _extra=extra,
      _data=data,  # Keep original for backwards compatibility
    )

  def __len__(self) -> int:
    """Return the number of rider sprints."""
    return len(self._riders)

  def __getitem__(
    self, index: int | slice
  ) -> ZPRiderSprint | list[ZPRiderSprint]:
    """Access rider sprints by index or slice."""
    return self._riders[index]

  def __iter__(self):
    """Iterate over rider sprints."""
    return iter(self._riders)

  def __repr__(self) -> str:
    """Return detailed representation."""
    return f'ZPRaceSprint(race_id={self.race_id}, riders={len(self._riders)})'

  def __str__(self) -> str:
    """Return human-readable string."""
    return (
      f'ZPRaceSprint(race_id={self.race_id}) with {len(self._riders)} riders'
    )

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields at race level."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields at race level."""
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return the sprint data as a dictionary.

    Returns typed field values directly, excluding internal fields.
    """
    return {
      'race_id': self.race_id,
      'data': [rider.asdict() for rider in self._riders],
    }

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of rider sprints as dictionaries."""
    return [rider.asdict() for rider in self._riders]

  def json(self) -> str:
    """Return JSON representation of sprint data."""
    return json.dumps(self._data, indent=2)
