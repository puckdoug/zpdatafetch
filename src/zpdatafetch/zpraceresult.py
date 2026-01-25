"""Represents race result data from Zwiftpower."""

import json
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from zpdatafetch.zp_utils import (
  convert_gender,
  extract_numeric,
  extract_value,
  format_time_hms,
  set_rider_category,
)


@dataclass(slots=True)
class ZPRiderFinish:
  """Represents a single rider's finish in a race result.

  Uses explicit typed fields for known API data with _extra dict
  to capture unexpected fields for forward compatibility.
  """

  # Core race result fields
  position: int = 0
  zwift_id: int = 0
  name: str = ''
  team_name: str | None = None
  team_id: int | None = None
  gender: str = ''  # "male" or "female"

  # Time and performance fields
  time: float = 0.0  # Finish time in seconds
  time_gun: float = 0.0  # Gun time in seconds
  time_hms: str = ''  # Finish time formatted as hh:mm:ss.sss
  time_gun_hms: str = ''  # Gun time formatted as hh:mm:ss.sss
  gap: float = 0.0  # Time gap to winner
  age: str = ''

  # Power metrics
  zftp: int = 0  # Zwift FTP value
  avg_power: float = 0.0  # Average power in watts
  avg_wkg: float = 0.0  # Average power per kg
  avg_hr: int = 0  # Average heart rate
  max_hr: int = 0  # Maximum heart rate
  np: float = 0.0  # Normalized Power

  # Wattage at different intervals
  w5: int = 0
  w15: int = 0
  w30: int = 0
  w60: int = 0
  w120: int = 0
  w300: int = 0
  w1200: int = 0

  # Wattage per kg at different intervals
  wkg5: float = 0.0
  wkg15: float = 0.0
  wkg30: float = 0.0
  wkg60: float = 0.0
  wkg120: float = 0.0
  wkg300: float = 0.0
  wkg1200: float = 0.0
  wkg_ftp: float = 0.0
  wftp: int = 0

  # Physical attributes
  height: int = 0  # Height in cm
  weight: float = 0.0  # Weight in kg

  # Skill and position metrics
  position_in_cat: int = 0  # Position in category
  skill: float = 0.0  # Skill rating
  skill_b: float = 0.0  # Secondary skill rating
  skill_gain: float = 0.0  # Skill gain
  zada: bool = False  # Zwift Academy status
  upg: bool = False  # Upgrade flag
  pts: int = 0  # Points awarded
  pen: str = ''  # Category/Penalty

  # Category and division
  category: str = ''  # Men's category (A, B, C, D)
  category_women: str = ''  # Women's category (A, B, C, D)
  hrm: bool = False  # Has heart rate monitor
  sweep: bool = False  # Sweep penalty flag
  lead: bool = False  # Lead penalty flag

  # Additional metrics
  uid: str = ''  # User identifier
  lag: float = 0.0  # Network lag
  vtta: float = 0.0  # veteran time trial association? - adjustment by age
  vttat: float = 0.0  # veteran time trial actual time? - pre-adjustment
  flag: int = 0  # Flag/status
  hrmax: int = 0  # Maximum heart rate
  hreff: int = 0  # Effective heart rate

  # Excluded fields - recognized but not explicitly handled (for potential future use)
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPRiderFinish':
    """Create instance from API response dict.

    Known fields are extracted with type coercion.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing rider result data

    Returns:
      ZPRiderFinish instance with parsed fields
    """
    known_fields = {
      'position',
      'zwift_id',
      'name',
      'team_name',
      'team',  # Alias for team_name
      'team_id',
      'gender',
      'time',
      'time_gun',
      'time_hms',
      'time_gun_hms',
      'gap',
      'age',
      'zftp',
      'avg_power',
      'avg_wkg',
      'avg_hr',
      'max_hr',
      'np',
      'w5',
      'w15',
      'w30',
      'w60',
      'w120',
      'w300',
      'w1200',
      'wkg5',
      'wkg15',
      'wkg30',
      'wkg60',
      'wkg120',
      'wkg300',
      'wkg1200',
      'wkg_ftp',
      'wftp',
      'height',
      'weight',
      'position_in_cat',
      'skill',
      'skill_b',
      'skill_gain',
      'zada',
      'upg',
      'pts',
      'pen',
      'sweep',
      'lead',
      'category',
      'category_women',
      'hrm',
      'uid',
      'lag',
      'vtta',
      'vttat',
      'flag',
      'hrmax',
      'hreff',
      # Field aliases (alternative names for the same data)
      'pos',
      'zwid',
      'tid',
      'tname',
      'div',
      'divw',
      'ftp',  # Alias for zftp
      # Used for gender conversion
      'male',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'power_type',
      'rank',
      'reg',
      'f',
      'friend',
      'late',
      'note',
      'penalty',
      'process',
      'set',
      'src',
      'type',
      'dq',
      'dnf',
      'dns',
    }

    # Determine gender from 'male' field
    male = data.get('male')
    gender = convert_gender(int(male)) if male is not None else ''

    # Determine category from 'div' field
    div = extract_numeric(data.get('div'), int, 0)
    category = set_rider_category(div)

    # Determine women's category from 'divw' field
    divw = extract_numeric(data.get('divw'), int, 0)
    category_women = set_rider_category(divw)

    # Determine if has heart rate monitor
    hrm_value = data.get('hrm')
    hrm = hrm_value == 1

    # Extract uid, lag, vtta, vttat, flag
    uid = str(data.get('uid', ''))
    lag = float(extract_numeric(data.get('lag'), float, 0.0))
    vtta = float(extract_numeric(data.get('vtta'), float, 0.0))
    vttat = float(extract_numeric(data.get('vttat'), float, 0.0))
    flag = int(extract_numeric(data.get('flag'), int, 0))

    # Extract first element from hrmax and hreff arrays
    hrmax_value = extract_value(data.get('hrmax'), 0)
    hrmax = int(extract_numeric(hrmax_value, int, 0))
    hreff_value = extract_value(data.get('hreff'), 0)
    hreff = int(extract_numeric(hreff_value, int, 0))

    # Extract and format time values
    time_seconds = float(
      extract_numeric(extract_value(data.get('time')), float, 0.0)
    )
    time_gun_seconds = float(
      extract_numeric(data.get('time_gun'), float, 0.0),
    )
    time_hms = format_time_hms(time_seconds)
    time_gun_hms = format_time_hms(time_gun_seconds)

    # Extract known fields from data and extras
    # Extract team_id as int or None
    team_id_raw = data.get('team_id') or data.get('tid')
    team_id: int | None = None
    if team_id_raw is not None:
      try:
        team_id = int(extract_value(team_id_raw, 0))
        if team_id == 0:
          team_id = None
      except (ValueError, TypeError):
        team_id = None

    return cls(
      position=int(extract_value(data.get('position') or data.get('pos'), 0)),
      zwift_id=int(extract_value(data.get('zwift_id') or data.get('zwid'), 0)),
      name=str(data.get('name', '')),
      team_name=data.get('team_name') or data.get('team') or data.get('tname'),
      team_id=team_id,
      gender=gender,
      time=time_seconds,
      time_gun=time_gun_seconds,
      time_hms=time_hms,
      time_gun_hms=time_gun_hms,
      gap=float(extract_numeric(data.get('gap'), float, 0.0)),
      age=str(data.get('age', '')),
      zftp=int(extract_numeric(data.get('zftp') or data.get('ftp'), int, 0)),
      avg_power=float(
        extract_numeric(extract_value(data.get('avg_power')), float, 0.0),
      ),
      avg_wkg=float(
        extract_numeric(extract_value(data.get('avg_wkg')), float, 0.0)
      ),
      avg_hr=int(extract_numeric(extract_value(data.get('avg_hr')), int, 0)),
      max_hr=int(extract_numeric(extract_value(data.get('max_hr')), int, 0)),
      np=float(extract_numeric(extract_value(data.get('np')), float, 0.0)),
      w5=int(extract_numeric(extract_value(data.get('w5')), int, 0)),
      w15=int(extract_numeric(extract_value(data.get('w15')), int, 0)),
      w30=int(extract_numeric(extract_value(data.get('w30')), int, 0)),
      w60=int(extract_numeric(extract_value(data.get('w60')), int, 0)),
      w120=int(extract_numeric(extract_value(data.get('w120')), int, 0)),
      w300=int(extract_numeric(extract_value(data.get('w300')), int, 0)),
      w1200=int(extract_numeric(extract_value(data.get('w1200')), int, 0)),
      wkg5=float(extract_numeric(extract_value(data.get('wkg5')), float, 0.0)),
      wkg15=float(
        extract_numeric(extract_value(data.get('wkg15')), float, 0.0)
      ),
      wkg30=float(
        extract_numeric(extract_value(data.get('wkg30')), float, 0.0)
      ),
      wkg60=float(
        extract_numeric(extract_value(data.get('wkg60')), float, 0.0)
      ),
      wkg120=float(
        extract_numeric(extract_value(data.get('wkg120')), float, 0.0)
      ),
      wkg300=float(
        extract_numeric(extract_value(data.get('wkg300')), float, 0.0)
      ),
      wkg1200=float(
        extract_numeric(extract_value(data.get('wkg1200')), float, 0.0)
      ),
      wkg_ftp=float(
        extract_numeric(extract_value(data.get('wkg_ftp')), float, 0.0)
      ),
      wftp=int(extract_numeric(extract_value(data.get('wftp')), int, 0)),
      height=int(extract_numeric(extract_value(data.get('height')), int, 0)),
      weight=float(
        extract_numeric(extract_value(data.get('weight')), float, 0.0)
      ),
      position_in_cat=int(extract_numeric(data.get('position_in_cat'), int, 0)),
      skill=float(extract_numeric(data.get('skill'), float, 0.0)),
      skill_b=float(extract_numeric(data.get('skill_b'), float, 0.0)),
      skill_gain=float(extract_numeric(data.get('skill_gain'), float, 0.0)),
      zada=int(data.get('zada', 0)) == 1,
      upg=int(data.get('upg', 0)) == 1,
      pts=int(extract_numeric(data.get('pts'), int, 0)),
      pen=str(data.get('category') or data.get('pen', '')),
      category=category,
      category_women=category_women,
      hrm=hrm,
      sweep=int(data.get('sweep', 0)) == 1,
      lead=int(data.get('lead', 0)) == 1,
      uid=uid,
      lag=lag,
      vtta=vtta,
      vttat=vttat,
      flag=flag,
      hrmax=hrmax,
      hreff=hreff,
      _excluded={
        k: v
        for k, v in data.items()
        if k not in known_fields and k in recognized_but_excluded
      },
      _extra={
        k: v
        for k, v in data.items()
        if k not in known_fields and k not in recognized_but_excluded
      },
    )

  def get_extra(self, key: str, default: Any = None) -> Any:
    """Access a single unknown field captured from API response.

    Args:
      key: Field name to access
      default: Default value if field not found

    Returns:
      Field value or default if not found
    """
    return self._extra.get(key, default)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields captured from API response.

    Useful for discovering new API fields not yet handled natively.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields recognized but not explicitly handled.

    These fields are identified as valid API fields but are not yet
    mapped to explicit attributes. Useful for discovering fields to add.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access for backwards compatibility.

    Args:
      key: Field name to access

    Returns:
      Field value

    Raises:
      KeyError: If field doesn't exist
    """
    try:
      return getattr(self, key)
    except AttributeError:
      raise KeyError(key)

  def __contains__(self, key: str) -> bool:
    """Check if field exists.

    Args:
      key: Field name to check

    Returns:
      True if field exists in dataclass or _extra
    """
    return hasattr(self, key)

  def asdict(self) -> dict[str, Any]:
    """Return the rider result data as a dictionary.

    Returns typed field values directly, excluding internal fields
    (_excluded and _extra).

    Returns:
      Dictionary containing typed rider data fields
    """
    result = asdict(self)
    result.pop('_extra', None)
    result.pop('_excluded', None)
    return result

  def json(self) -> str:
    """Return JSON representation of rider result data.

    Returns:
      JSON string with 2-space indentation
    """
    return json.dumps(self.asdict(), indent=2)


@dataclass(slots=True)
class ZPRaceResult(Sequence):
  """Collection of rider finishes for a race.

  Stores race metadata and implements Sequence protocol for accessing
  rider finishes. Uses explicit fields for known API data with _extra
  dict to capture unexpected fields.

  Attributes:
    race_id: Race identifier
    event_name: Race event name
    event_date: Race date/timestamp
    _riders: List of rider finishes (internal)
    _extra: Captures unknown fields from API (internal)
  """

  # Metadata fields
  race_id: int = 0
  event_name: str = ''
  event_date: str = ''

  # Collection of riders (not in __init__, set via from_dict)
  _riders: list[ZPRiderFinish] = field(
    default_factory=list,
    repr=False,
    init=False,
  )

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(
    default_factory=dict,
    repr=False,
    init=False,
  )

  # Extra fields from API
  _extra: dict[str, Any] = field(
    default_factory=dict,
    repr=False,
    init=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPRaceResult':
    """Create instance from API response dict.

    Parses nested rider data and captures unknown fields.

    Args:
      data: Dictionary containing race result data

    Returns:
      ZPRaceResult instance with parsed fields and riders
    """
    known_fields = {'race_id', 'event_name', 'event_date', 'data', 'zid'}

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'status',
      'message',
      'event_id',
      'start_time',
      'end_time',
      'route',
      'laps',
    }

    # Parse rider list from nested "data" key
    riders = [ZPRiderFinish.from_dict(r) for r in data.get('data', [])]

    # Classify remaining fields
    excluded = {}
    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        if key in recognized_but_excluded:
          excluded[key] = value
        else:
          extra[key] = value

    # Create instance with metadata
    instance = cls(
      race_id=int(data.get('race_id') or data.get('zid', 0)),
      event_name=str(data.get('event_name', '')),
      event_date=str(data.get('event_date', '')),
    )

    # Set riders and field classification dicts (not in __init__)
    instance._riders = riders
    instance._excluded = excluded
    instance._extra = extra

    return instance

  # Sequence protocol implementation
  def __len__(self) -> int:
    """Return the number of riders in the result.

    Returns:
      Number of riders
    """
    return len(self._riders)

  def __getitem__(self, index: int) -> ZPRiderFinish:  # type: ignore[override]
    """Access rider finish by index.

    Args:
      index: Integer index

    Returns:
      Single rider

    Raises:
      IndexError: If index out of range
    """
    return self._riders[index]

  def __iter__(self) -> Iterator[ZPRiderFinish]:
    """Iterate over rider finishes.

    Returns:
      Iterator over ZPRiderFinish objects
    """
    return iter(self._riders)

  def __repr__(self) -> str:
    """Return detailed representation.

    Returns:
      String representation showing metadata and rider count
    """
    return (
      f'ZPRaceResult(race_id={self.race_id}, event_name={self.event_name!r}, '
      f'event_date={self.event_date!r}, riders={len(self._riders)})'
    )

  def __str__(self) -> str:
    """Return human-readable string.

    Returns:
      String with race info and rider count
    """
    return f'ZPRaceResult with {len(self._riders)} riders'

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to race-level result fields (backwards compat).

    This is called only when normal attribute lookup fails.

    Args:
      name: Field name to access

    Returns:
      Field value from _extra

    Raises:
      AttributeError: If field doesn't exist
    """
    if name.startswith('_'):
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      )
    try:
      return self._extra[name]
    except KeyError:
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      )

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields captured from API response.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields recognized but not explicitly handled.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def asdict(self) -> dict[str, Any]:
    """Return the result data as a dictionary.

    Returns typed field values directly, excluding internal fields.

    Returns:
      Dictionary containing race metadata and riders
    """
    return {
      'race_id': self.race_id,
      'event_name': self.event_name,
      'event_date': self.event_date,
      'data': [rider.asdict() for rider in self._riders],
    }

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of rider results as dictionaries.

    Returns:
      List of rider dictionaries
    """
    return [rider.asdict() for rider in self._riders]

  def json(self) -> str:
    """Return JSON representation of result data.

    Returns:
      JSON string with 2-space indentation
    """
    return json.dumps(self.asdict(), indent=2)
