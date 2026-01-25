"""Represents a single race finish from a cyclist's race history."""

import json
from dataclasses import dataclass, field
from typing import Any

from zpdatafetch.zp_utils import (
  convert_gender,
  convert_timestamp_to_iso8601,
  format_time_hms,
  set_rider_category,
)


@dataclass(slots=True)
class ZPRaceFinish:
  """Represents a single race finish/result.

  Wraps a single race entry from the cyclist race log with convenient
  typed field access to race data.

  Attributes:
    All race data fields are accessible as explicit typed attributes, including:
    - zwift_id: Rider's Zwift ID (mapped from 'zid')
    - event_title: Race name
    - event_date: Race timestamp (ISO-8601 format)
    - position: Overall position (mapped from 'pos')
    - position_in_cat: Position in category
    - category: Rider's category letter (A-E, converted from 'div')
    - category_women: Women's category letter (A-E, converted from 'divw')
    - avg_power, avg_wkg: Performance metrics
    - And all other fields from the race data

  Field Transformations:
    Field Aliases (backwards compatibility):
    - 'zid' or 'zwid' → 'zwift_id'
    - 'pos' → 'position'
    - 'ftp' → 'zftp'
    - 'tid' → 'team_id'
    - 'tname' → 'team_name'

    Conversions:
    - 'div' → 'category' (0/10/20/30/40 → empty/A/B/C/D)
    - 'divw' → 'category_women' (0/10/20/30/40 → empty/A/B/C/D)
    - 'male' → 'gender' (1→male, 0→female)
    - 'time' → 'time' (seconds value) + 'time_hms' (formatted as hh:mm:ss.sss)
    - 'time_gun' → 'time_gun' (seconds value) + 'time_gun_hms' (formatted as hh:mm:ss.sss)
    - 'event_date' → 'event_date' (Unix timestamp → ISO-8601 UTC format, replaces original)
  """

  # Core race result fields
  zwift_id: int = 0
  name: str = ''
  position: int = 0
  team_id: int | None = None
  team_name: str | None = None
  gender: str = ''  # "male" or "female"
  category: str = ''  # Men's category (A-E)
  category_women: str = ''  # Women's category (A-E)

  # Time and performance fields
  time: float = 0.0  # Finish time in seconds
  time_gun: float = 0.0  # Gun time in seconds
  time_hms: str = ''  # Finish time formatted as hh:mm:ss.sss
  time_gun_hms: str = ''  # Gun time formatted as hh:mm:ss.sss
  gap: float = 0.0  # Time gap to winner

  # Event metadata
  event_title: str = ''
  event_date: str = ''  # ISO-8601 format

  # Power metrics
  zftp: int = 0  # Zwift's internal FTP (not actual FTP)
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
  age: str = ''

  # Numeric timestamp for comparisons (not in repr)
  _event_date_timestamp: float = field(default=0.0, repr=False)

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPRaceFinish':
    """Create instance from API response dict.

    Transforms field names, converts numeric codes to readable values, and
    extracts array fields. Unknown fields are captured in _excluded and _extra
    for forward compatibility.

    Args:
      data: Dictionary containing race result data

    Returns:
      ZPRaceFinish instance with parsed fields
    """
    # Fields that are stored as [value, flag] arrays - extract first element
    # (Not used directly, but kept for documentation of which fields may be arrays)

    # Field name mappings and aliases (old_name -> new_name)
    # Aliases allow backwards compatibility - we check for both old and new names
    field_aliases = {
      'zid': 'zwift_id',  # Old API field name
      'zwid': 'zwift_id',  # Alternative old API field name
      'pos': 'position',  # Old API field name
      'ftp': 'zftp',  # Old API field name
      'tid': 'team_id',  # Old API field name
      'tname': 'team_name',  # Old API field name
    }

    # Define excluded field names upfront (recognized but not explicit)
    excluded_field_names = {
      'DT_RowId',
      'friend',
      'pt',
      'label',
      'tc',
      'tbc',
      'tbd',
      'reg',
      'fl',
      'info',
      'info_note',
      'strike',
      'f_t',
      'rt',
      'dur',
      'pts_pos',
      'pts',
      'is_guess',
      'note',
      'src',
      'power_type',
      'zeff',
      'info_notes',
    }

    # Known field names (explicit + aliases + special transformations)
    known_fields = {
      'zwift_id',
      'zid',
      'zwid',
      'name',
      'position',
      'pos',
      'team_id',
      'tid',
      'team_name',
      'tname',
      'gender',
      'male',
      'category',
      'category_women',
      'div',
      'divw',
      'time',
      'time_gun',
      'time_hms',
      'time_gun_hms',
      'gap',
      'event_title',
      'event_date',
      'zftp',
      'ftp',
      'avg_power',
      'avg_wkg',
      'avg_hr',
      'max_hr',
      'hrmax',
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
      'age',
    }

    # Extract and convert key values before main loop
    def extract_array_value(value: Any) -> Any:
      """Extract first element from array if applicable."""
      if isinstance(value, list) and len(value) > 0:
        return value[0]
      return value

    # Category conversions
    div_value = extract_array_value(data.get('div', 0))
    div_value = int(div_value) if div_value else 0
    category = set_rider_category(div_value)

    divw_value = extract_array_value(data.get('divw', 0))
    divw_value = int(divw_value) if divw_value else 0
    category_women = set_rider_category(divw_value)

    # Gender conversion
    male_value = extract_array_value(data.get('male'))
    male_value = int(male_value) if male_value is not None else None
    gender = convert_gender(male_value) if male_value is not None else ''

    # Time conversions
    time_value = extract_array_value(data.get('time', 0))
    time_value = float(time_value) if time_value else 0.0
    time_hms = format_time_hms(time_value)

    time_gun_value = extract_array_value(data.get('time_gun', 0))
    time_gun_value = float(time_gun_value) if time_gun_value else 0.0
    time_gun_hms = format_time_hms(time_gun_value)

    # Event date conversion (and preserve numeric timestamp for filtering)
    event_date_value = extract_array_value(data.get('event_date'))
    if not isinstance(event_date_value, str):
      event_date_value = float(event_date_value) if event_date_value else 0.0
    event_date_timestamp = (
      float(event_date_value)
      if isinstance(event_date_value, (int, float))
      else 0.0
    )
    event_date = convert_timestamp_to_iso8601(event_date_value)

    # Helper to get value with alias support
    def get_aliased_value(key: str) -> Any:
      """Get value checking original key and aliases."""
      if key in data:
        return data[key]
      # Check for aliased versions
      for alias, mapped in field_aliases.items():
        if mapped == key and alias in data:
          return data[alias]
      return None

    # Collect excluded and extra fields
    excluded = {}
    extra = {}

    for key, value in data.items():
      if key in excluded_field_names:
        excluded[key] = value
      elif key not in known_fields:
        extra[key] = value

    # Extract basic fields (with array extraction as needed)
    def get_field_value(key: str, default: Any, field_type: type) -> Any:
      """Get field value with alias support and type conversion."""
      value = get_aliased_value(key)
      if value is None:
        return default
      # Extract from array if needed
      value = extract_array_value(value)
      try:
        return field_type(value) if value is not None else default
      except (ValueError, TypeError):
        return default

    # Extract team_id as int or None
    team_id_raw = get_aliased_value('team_id')
    team_id: int | None = None
    if team_id_raw is not None and team_id_raw != '':
      try:
        team_id = int(team_id_raw)
        if team_id == 0:
          team_id = None
      except (ValueError, TypeError):
        team_id = None

    return cls(
      zwift_id=get_field_value('zwift_id', 0, int),
      name=str(get_aliased_value('name') or ''),
      position=get_field_value('position', 0, int),
      team_id=team_id,
      team_name=str(get_aliased_value('team_name') or '') or None,
      gender=gender,
      category=category,
      category_women=category_women,
      time=time_value,
      time_gun=time_gun_value,
      time_hms=time_hms,
      time_gun_hms=time_gun_hms,
      gap=get_field_value('gap', 0.0, float),
      event_title=str(get_aliased_value('event_title') or ''),
      event_date=event_date,
      zftp=get_field_value('zftp', 0, int),
      avg_power=get_field_value('avg_power', 0.0, float),
      avg_wkg=get_field_value('avg_wkg', 0.0, float),
      avg_hr=get_field_value('avg_hr', 0, int),
      max_hr=get_field_value('max_hr', 0, int),
      np=get_field_value('np', 0.0, float),
      w5=get_field_value('w5', 0, int),
      w15=get_field_value('w15', 0, int),
      w30=get_field_value('w30', 0, int),
      w60=get_field_value('w60', 0, int),
      w120=get_field_value('w120', 0, int),
      w300=get_field_value('w300', 0, int),
      w1200=get_field_value('w1200', 0, int),
      wkg5=get_field_value('wkg5', 0.0, float),
      wkg15=get_field_value('wkg15', 0.0, float),
      wkg30=get_field_value('wkg30', 0.0, float),
      wkg60=get_field_value('wkg60', 0.0, float),
      wkg120=get_field_value('wkg120', 0.0, float),
      wkg300=get_field_value('wkg300', 0.0, float),
      wkg1200=get_field_value('wkg1200', 0.0, float),
      wkg_ftp=get_field_value('wkg_ftp', 0.0, float),
      wftp=get_field_value('wftp', 0, int),
      height=get_field_value('height', 0, int),
      weight=get_field_value('weight', 0.0, float),
      position_in_cat=get_field_value('position_in_cat', 0, int),
      skill=get_field_value('skill', 0.0, float),
      age=str(get_aliased_value('age') or ''),
      _event_date_timestamp=event_date_timestamp,
      _excluded=excluded,
      _extra=extra,
    )

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to race data for backwards compatibility.

    Args:
      key: Field name to access

    Returns:
      Value of the field

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
      True if field exists in dataclass or _excluded/_extra
    """
    return hasattr(self, key) or key in self._excluded or key in self._extra

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields for this race.

    These are fields documented in the API but not yet promoted to
    explicit typed attributes.

    Returns:
      Dictionary of recognized but unhandled fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields from API response for this race.

    These fields are not yet recognized by the application,
    likely from recent API changes.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return the underlying race data as a dictionary.

    Reconstructs dict with all fields in a usable format.

    Returns:
      Dictionary containing all race data
    """
    from dataclasses import asdict as dataclass_asdict

    result = dataclass_asdict(self)
    # Remove internal fields from the dict representation
    result.pop('_event_date_timestamp', None)
    result.pop('_excluded', None)
    result.pop('_extra', None)
    return result

  def json(self) -> str:
    """Return JSON representation of race finish data.

    Returns:
      JSON string with 2-space indentation
    """
    return json.dumps(self.asdict(), indent=2)
