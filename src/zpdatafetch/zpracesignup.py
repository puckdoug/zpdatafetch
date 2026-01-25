"""Represents race signup data from Zwiftpower."""

import json
from dataclasses import dataclass, field
from typing import Any

from zpdatafetch.zp_utils import (
  convert_gender,
  convert_label_to_pen,
  extract_value,
  set_rider_category,
)


def convert_bool_field(value: Any) -> bool:
  """Convert various representations to boolean.

  Handles:
  - 0/1 integers
  - String '0'/'1'
  - None/empty values
  - Already boolean values
  """
  if value is None or value == '':
    return False
  if isinstance(value, bool):
    return value
  if isinstance(value, int):
    return value != 0
  if isinstance(value, str):
    return value.lower() not in ('0', 'false', '')
  return bool(value)


@dataclass(slots=True)
class ZPcp:
  """Represents critical power data with rank, value, and percentage.

  Critical power fields from the API contain 3 elements:
  - rank: Ranking/position (int)
  - value: The actual power value (float for watts/wkg)
  - percentage: Percentage value (float)

  Attributes:
    rank: Ranking or position indicator
    value: The critical power value (watts or watts/kg)
    percentage: Percentage value associated with the metric
  """

  rank: int = 0
  value: float = 0.0
  percentage: float = 0.0

  @classmethod
  def from_list(cls, data: Any) -> 'ZPcp':
    """Create ZPcp instance from array format [rank, value, percentage].

    Args:
      data: List/array with 3 elements [rank, value, percentage]

    Returns:
      ZPcp instance with parsed fields
    """
    if not data or not isinstance(data, (list, tuple)):
      return cls(rank=0, value=0.0, percentage=0.0)

    try:
      rank = int(data[0]) if len(data) > 0 else 0
      # Value might be string with comma formatting ('1,212') - strip it
      value_str = str(data[1]) if len(data) > 1 else '0'
      value = float(value_str.replace(',', ''))
      percentage = float(data[2]) if len(data) > 2 else 0.0
      return cls(rank=rank, value=value, percentage=percentage)
    except (ValueError, IndexError, TypeError):
      return cls(rank=0, value=0.0, percentage=0.0)

  def __getitem__(self, index: int) -> Any:
    """Support array indexing: x[0] → rank, x[1] → value, x[2] → percentage."""
    if index == 0:
      return self.rank
    if index == 1:
      return self.value
    if index == 2:
      return self.percentage
    raise IndexError(f'ZPcp index out of range: {index}')

  def __iter__(self):
    """Support iteration over cp data."""
    return iter((self.rank, self.value, self.percentage))

  def __repr__(self) -> str:
    """Return representation matching array format."""
    return f'ZPcp({self.rank}, {self.value}, {self.percentage})'

  def as_list(self) -> list[Any]:
    """Return as list in original format [rank, value, percentage]."""
    return [self.rank, self.value, self.percentage]


@dataclass(slots=True)
class ZPRiderSignup:
  """Represents a single rider's signup for a race.

  Stores rider signup data with explicit typed fields and captures
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
      category: Registration category (A+/A/B/C/D or empty)
      category_women: Women's category
      reg: Registration status (1=registered)
      pen: Race-specific pen/category letter (A/B/C/D/E or empty)
      rank: Ranking/rating value
      zada: Zwift Academy status (boolean)

    Team information:
      team_id: Team ID
      team_name: Team name

    Power and performance data:
      zftp: Functional Threshold Power (FTP)
      weight_array: Weight as [value, flag] array format
      height_array: Height as [value, flag] array format
      eff: Efficiency rating
      skill: Overall skill rating
      skill_power: Power component of skill
      skill_seg: Segment skill component
      skill_race: Race skill component
      skill_pos: Position/placement skill component
      rank_numeric: Numeric rank value

    Penalty flags:
      wrg_cat: Wrong category flag (boolean)
      sweep: Sweep penalty flag (boolean)
      lead: Lead penalty flag (boolean)

    Critical power data:
      cp_15_watts: Critical power 15 seconds (watts)
      cp_15_wkg: Critical power 15 seconds (watts/kg)
      cp_60_watts: Critical power 60 seconds (watts)
      cp_60_wkg: Critical power 60 seconds (watts/kg)
      cp_300_watts: Critical power 300 seconds (watts)
      cp_300_wkg: Critical power 300 seconds (watts/kg)
      cp_1200_watts: Critical power 1200 seconds (watts)
      cp_1200_wkg: Critical power 1200 seconds (watts/kg)
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
  category_women: str = ''
  reg: int = 0
  pen: str = ''
  rank: str = ''
  zada: bool = False

  # Team information
  team_id: int | None = None
  team_name: str | None = None

  # Power and performance data
  zftp: int = 0
  eff: str = ''
  skill: int = 0
  skill_power: int = 0
  skill_seg: int = 0
  skill_race: int = 0
  skill_pos: int = 0

  # Penalty flags
  wrg_cat: bool = False
  sweep: bool = False
  lead: bool = False

  # Critical power data (watts and watts/kg) - each contains [rank, value, percentage]
  cp_15_watts: ZPcp = field(default_factory=ZPcp)
  cp_15_wkg: ZPcp = field(default_factory=ZPcp)
  cp_60_watts: ZPcp = field(default_factory=ZPcp)
  cp_60_wkg: ZPcp = field(default_factory=ZPcp)
  cp_300_watts: ZPcp = field(default_factory=ZPcp)
  cp_300_wkg: ZPcp = field(default_factory=ZPcp)
  cp_1200_watts: ZPcp = field(default_factory=ZPcp)
  cp_1200_wkg: ZPcp = field(default_factory=ZPcp)

  # Field classification dicts
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPRiderSignup':
    """Create instance from API response dict.

    Known fields are extracted with type coercion and transformations.
    Field aliases are checked for backwards compatibility.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing rider signup data from API response

    Returns:
      ZPRiderSignup instance with parsed fields
    """
    known_fields = {
      'zwid',
      'name',
      'age',
      'gender',
      'flag',
      'height',
      'weight',
      'div',
      'divw',
      'reg',
      'label',
      'rank',
      'zada',
      'tid',
      'tname',
      'ftp',
      'eff',
      'skill',
      'skill_power',
      'skill_seg',
      'skill_race',
      'skill_pos',
      'wrg_cat',
      'sweep',
      'lead',
      'cp_15_watts',
      'cp_15_wkg',
      'cp_60_watts',
      'cp_60_wkg',
      'cp_300_watts',
      'cp_300_wkg',
      'cp_1200_watts',
      'cp_1200_wkg',
      'watts',
      'msec',
    }

    # Fields to exclude (recognized from API but not explicitly handled)
    recognized_but_excluded = {
      'tbd',
      'tbc',
      'tc',
      'topen',
      'pt',
      's',
      'friend',
      'events',
    }

    # Extract known fields with proper type conversions
    zwift_id = int(data.get('zwid', 0))
    name = str(data.get('name', ''))
    age = str(data.get('age', ''))

    # Gender conversion (handles both 'm'/'f' strings and 0/1 integers)
    gender_raw = data.get('gender', '')
    gender = convert_gender(gender_raw) if gender_raw != '' else ''

    flag = str(data.get('flag', ''))

    # Height and weight from array format or direct value
    height_raw = data.get('height', 0)
    height = (
      int(extract_value(height_raw, 0)) if extract_value(height_raw, 0) else 0
    )

    weight_raw = data.get('weight', 0)
    weight = float(extract_value(weight_raw, 0))

    # Category with division mapping (div: 0/5/10/20/30/40 -> empty/A+/A/B/C/D)
    category = ''
    if 'category' in data:
      category = str(data.get('category', ''))
    elif 'div' in data:
      category = set_rider_category(int(data.get('div', 0)))

    # Women's category
    category_women = ''
    if 'divw' in data:
      category_women = set_rider_category(int(data.get('divw', 0)))

    # Registration and status
    reg = int(data.get('reg', 0))
    pen = convert_label_to_pen(int(data.get('label', 0)))
    rank = str(data.get('rank', ''))
    zada = convert_bool_field(data.get('zada', 0))

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

    # Power and performance
    zftp_raw = data.get('ftp', 0)
    try:
      zftp = int(zftp_raw) if zftp_raw else 0
    except (ValueError, TypeError):
      zftp = 0
    eff = str(data.get('eff', ''))
    skill = int(data.get('skill', 0))
    skill_power = int(data.get('skill_power', 0))
    skill_seg = int(data.get('skill_seg', 0))
    skill_race = int(data.get('skill_race', 0))
    skill_pos = int(data.get('skill_pos', 0))

    # Penalty flags
    wrg_cat = convert_bool_field(data.get('wrg_cat', 0))
    sweep = convert_bool_field(data.get('sweep', 0))
    lead = convert_bool_field(data.get('lead', 0))

    # Critical power data (extract from [value1, value2, value3] format)
    # Critical power fields are [rank, value, percentage] arrays
    cp_15_watts = ZPcp.from_list(data.get('cp_15_watts'))
    cp_15_wkg = ZPcp.from_list(data.get('cp_15_wkg'))
    cp_60_watts = ZPcp.from_list(data.get('cp_60_watts'))
    cp_60_wkg = ZPcp.from_list(data.get('cp_60_wkg'))
    cp_300_watts = ZPcp.from_list(data.get('cp_300_watts'))
    cp_300_wkg = ZPcp.from_list(data.get('cp_300_wkg'))
    cp_1200_watts = ZPcp.from_list(data.get('cp_1200_watts'))
    cp_1200_wkg = ZPcp.from_list(data.get('cp_1200_wkg'))

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
      category_women=category_women,
      reg=reg,
      pen=pen,
      rank=rank,
      zada=zada,
      team_id=team_id,
      team_name=team_name,
      zftp=zftp,
      eff=eff,
      skill=skill,
      skill_power=skill_power,
      skill_seg=skill_seg,
      skill_race=skill_race,
      skill_pos=skill_pos,
      wrg_cat=wrg_cat,
      sweep=sweep,
      lead=lead,
      cp_15_watts=cp_15_watts,
      cp_15_wkg=cp_15_wkg,
      cp_60_watts=cp_60_watts,
      cp_60_wkg=cp_60_wkg,
      cp_300_watts=cp_300_watts,
      cp_300_wkg=cp_300_wkg,
      cp_1200_watts=cp_1200_watts,
      cp_1200_wkg=cp_1200_wkg,
      _excluded=excluded,
      _extra=extra,
    )

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to signup data for backwards compatibility."""
    # Check explicit fields first (via dataclass __dict__)
    if hasattr(self, key):
      return getattr(self, key)
    # Check excluded and extra dicts
    if key in self._excluded:
      return self._excluded[key]
    if key in self._extra:
      return self._extra[key]
    raise KeyError(key)

  def __contains__(self, key: str) -> bool:
    """Check if a key exists in the signup data."""
    return hasattr(self, key) or key in self._excluded or key in self._extra

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields (candidates for future promotion)."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields (likely from recent API changes)."""
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return the signup data as a dictionary.

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
      'category_women': self.category_women,
      'reg': self.reg,
      'pen': self.pen,
      'rank': self.rank,
      'zada': self.zada,
      'team_id': self.team_id,
      'team_name': self.team_name,
      'zftp': self.zftp,
      'eff': self.eff,
      'skill': self.skill,
      'skill_power': self.skill_power,
      'skill_seg': self.skill_seg,
      'skill_race': self.skill_race,
      'skill_pos': self.skill_pos,
      'wrg_cat': self.wrg_cat,
      'sweep': self.sweep,
      'lead': self.lead,
      'cp_15_watts': self.cp_15_watts.as_list(),
      'cp_15_wkg': self.cp_15_wkg.as_list(),
      'cp_60_watts': self.cp_60_watts.as_list(),
      'cp_60_wkg': self.cp_60_wkg.as_list(),
      'cp_300_watts': self.cp_300_watts.as_list(),
      'cp_300_wkg': self.cp_300_wkg.as_list(),
      'cp_1200_watts': self.cp_1200_watts.as_list(),
      'cp_1200_wkg': self.cp_1200_wkg.as_list(),
    }

  def json(self) -> str:
    """Return JSON representation of signup data."""
    return json.dumps(self.asdict(), indent=2)


@dataclass(slots=True)
class ZPRaceSignup:
  """Collection of rider signups for a race.

  Stores race-level signup metadata and a list of individual rider signups.
  Provides convenient iteration and indexing operations.

  Attributes:
    race_id: The race ID (may be injected from URL parameter)
    And other race-level fields
  """

  # Race-level metadata fields
  race_id: int = 0

  # Collection of rider signups
  _riders: list[ZPRiderSignup] = field(default_factory=list, repr=False)

  # Field classification dicts
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  # Original data dict for backwards compatibility
  _data: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPRaceSignup':
    """Create instance from API response dict.

    Parses race-level fields and creates ZPRiderSignup objects
    from the nested 'data' array.

    Args:
      data: Dictionary containing race signup data from API response

    Returns:
      ZPRaceSignup instance with parsed fields
    """
    known_fields = {'data', 'race_id'}
    recognized_but_excluded = {'status', 'message', 'event_name'}

    # Parse rider list from nested "data" key
    riders = []
    for rider_data in data.get('data', []):
      riders.append(ZPRiderSignup.from_dict(rider_data))

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
    """Return the number of riders signed up."""
    return len(self._riders)

  def __getitem__(
    self, index: int | slice
  ) -> ZPRiderSignup | list[ZPRiderSignup]:
    """Access rider signups by index or slice."""
    return self._riders[index]

  def __iter__(self):
    """Iterate over rider signups."""
    return iter(self._riders)

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to race-level signup fields for backwards compatibility."""
    if name.startswith('_'):
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'"
      )
    # Check data dict for backwards compatibility
    if name in self._data:
      return self._data[name]
    raise AttributeError(
      f"'{type(self).__name__}' object has no attribute '{name}'"
    )

  def __repr__(self) -> str:
    """Return detailed representation."""
    return f'ZPRaceSignup(race_id={self.race_id}, riders={len(self._riders)})'

  def __str__(self) -> str:
    """Return human-readable string."""
    return f'ZPRaceSignup(race_id={self.race_id}) with {len(self._riders)} riders signed up'

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields at race level."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields at race level."""
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return the signup data as a dictionary.

    Returns typed field values directly, excluding internal fields.
    """
    return {
      'race_id': self.race_id,
      'data': [rider.asdict() for rider in self._riders],
    }

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of rider signups as dictionaries."""
    return [rider.asdict() for rider in self._riders]

  def json(self) -> str:
    """Return JSON representation of signup data."""
    return json.dumps(self._data, indent=2)
