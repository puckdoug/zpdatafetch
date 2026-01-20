"""Represents a single race finish from a cyclist's race history."""

from typing import Any

from zpdatafetch.zp_utils import (
  convert_gender,
  convert_timestamp_to_iso8601,
  format_time_hms,
  set_rider_category,
)


class ZPRaceFinish:
  """Represents a single race finish/result.

  Wraps a single race entry from the cyclist race log with convenient
  attribute access to race data.

  Attributes:
    All race data fields are accessible as attributes, including:
    - zwift_id: Rider's Zwift ID (mapped from 'zid')
    - event_title: Race name
    - event_date: Race timestamp
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

  # Fields that are stored as [value, flag] arrays that should be cleaned to just value
  _ARRAY_FIELDS = {
    'time',
    'height',
    'avg_hr',
    'max_hr',
    'hrmax',
    'weight',
    'np',
    'hrr',
    'hreff',
    'avg_power',
    'avg_wkg',
    'wkg_ftp',
    'wftp',
    'wkg1200',
    'wkg300',
    'wkg120',
    'wkg60',
    'wkg30',
    'wkg15',
    'wkg5',
    'w1200',
    'w300',
    'w120',
    'w60',
    'w30',
    'w15',
    'w5',
  }

  def __init__(self, race_data: dict[str, Any] | None = None) -> None:
    """Initialize a RaceFinish from race data dictionary.

    Cleans up array fields by extracting the first element from fields
    that are stored as [value, flag] pairs. Also applies field name mappings
    for consistency (ftp→zftp, zid→zwift_id, pos→position).

    Args:
      race_data: Dictionary containing race result data.
                 If None, creates an empty race finish object.
    """
    # Clean up the data by extracting first element from array fields
    data = race_data if race_data is not None else {}
    cleaned_data = {}

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

    # Define excluded field names upfront
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
      'position_in_cat',
    }

    # Collect excluded fields and clean data
    self._excluded: dict[str, Any] = {}
    self._extra: dict[str, Any] = {}

    # Extract numeric codes for category and gender conversions before main loop
    div_value = data.get('div', 0)
    if isinstance(div_value, list) and len(div_value) > 0:
      div_value = div_value[0]
    div_value = int(div_value) if div_value else 0

    divw_value = data.get('divw', 0)
    if isinstance(divw_value, list) and len(divw_value) > 0:
      divw_value = divw_value[0]
    divw_value = int(divw_value) if divw_value else 0

    male_value = data.get('male')
    if isinstance(male_value, list) and len(male_value) > 0:
      male_value = male_value[0]
    male_value = int(male_value) if male_value is not None else None

    # Extract time values (may be arrays) for time_hms conversions
    time_value = data.get('time')
    if isinstance(time_value, list) and len(time_value) > 0:
      time_value = time_value[0]
    time_value = float(time_value) if time_value else 0.0

    time_gun_value = data.get('time_gun')
    if isinstance(time_gun_value, list) and len(time_gun_value) > 0:
      time_gun_value = time_gun_value[0]
    time_gun_value = float(time_gun_value) if time_gun_value else 0.0

    # Extract event_date for ISO-8601 conversion
    event_date_value = data.get('event_date')
    if isinstance(event_date_value, list) and len(event_date_value) > 0:
      event_date_value = event_date_value[0]
    # Handle both numeric timestamps and already-formatted ISO-8601 strings
    if not isinstance(event_date_value, str):
      event_date_value = float(event_date_value) if event_date_value else 0.0

    for key, value in data.items():
      # Skip excluded fields - store in _excluded instead
      if key in excluded_field_names:
        self._excluded[key] = value
        continue

      # Skip div, divw, and male - they're converted to other fields
      if key in ('div', 'divw', 'male'):
        continue

      # Skip time and time_gun in the loop - they'll be processed specially
      # (event_date will be processed normally, but we'll also add event_date_iso)
      if key in ('time', 'time_gun'):
        continue

      # Handle array fields extraction
      if key in self._ARRAY_FIELDS and isinstance(value, list) and len(value) > 0:
        cleaned_value = value[0]
      else:
        cleaned_value = value

      # Apply field name aliases - store only under aliased name if one exists
      target_key = field_aliases.get(key, key)

      # Don't overwrite if we already have the target key from a preferred source
      # (e.g., if we have 'zwift_id', don't overwrite with 'zid' or 'zwid')
      if target_key not in cleaned_data:
        cleaned_data[target_key] = cleaned_value

    # Add converted category fields
    cleaned_data['category'] = set_rider_category(div_value)
    cleaned_data['category_women'] = set_rider_category(divw_value)

    # Add gender field from male conversion
    if male_value is not None:
      cleaned_data['gender'] = convert_gender(male_value)

    # Add time and time_hms fields (keep both original seconds and formatted)
    cleaned_data['time'] = time_value
    cleaned_data['time_hms'] = format_time_hms(time_value)

    # Add time_gun and time_gun_hms fields (keep both original seconds and formatted)
    cleaned_data['time_gun'] = time_gun_value
    cleaned_data['time_gun_hms'] = format_time_hms(time_gun_value)

    # Convert event_date to ISO-8601 format (replaces Unix timestamp)
    cleaned_data['event_date'] = convert_timestamp_to_iso8601(event_date_value)

    self._data = cleaned_data

    # Store numeric timestamp separately for time comparisons (e.g., days_last filtering)
    # This preserves the original numeric timestamp even though event_date is now a string
    if isinstance(event_date_value, str):
      # If it's a string, we can't recover the original timestamp, so use 0
      self._event_date_timestamp = 0.0
    else:
      # Convert to float for numeric comparisons
      self._event_date_timestamp = float(event_date_value) if event_date_value else 0.0

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to race data fields.

    Args:
      name: Field name to access

    Returns:
      Value of the field

    Raises:
      AttributeError: If field doesn't exist
    """
    if name.startswith('_'):
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    try:
      return self._data[name]
    except KeyError:
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to race data.

    Args:
      key: Field name to access

    Returns:
      Value of the field
    """
    return self._data[key]

  def __repr__(self) -> str:
    """Return detailed representation showing all race data.

    Returns:
      String in format: RaceFinish(key=value, key=value, ...)
    """
    items = ', '.join(f'{k}={v!r}' for k, v in self._data.items())
    return f'ZPRaceFinish({items})'

  def __str__(self) -> str:
    """Return human-readable string with all race data.

    Returns:
      Multi-line string showing all fields
    """
    lines = ['ZPRaceFinish(']
    for key, value in self._data.items():
      lines.append(f'  {key}={value!r},')
    lines.append(')')
    return '\n'.join(lines)

  def asdict(self) -> dict[str, Any]:
    """Return the underlying race data as a dictionary.

    Returns:
      Dictionary containing all race data
    """
    return self._data

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
