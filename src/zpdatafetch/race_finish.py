"""Represents a single race finish from a cyclist's race history."""

from typing import Any


class RaceFinish:
  """Represents a single race finish/result.

  Wraps a single race entry from the cyclist race log with convenient
  attribute access to race data.

  Attributes:
    All race data fields are accessible as attributes, including:
    - zid: Race ID
    - event_title: Race name
    - event_date: Race timestamp
    - pos: Overall position
    - position_in_cat: Position in category
    - avg_power, avg_wkg: Performance metrics
    - And all other fields from the race data
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

  def __init__(self, race_data: dict[str, Any]) -> None:
    """Initialize a RaceFinish from race data dictionary.

    Cleans up array fields by extracting the first element from fields
    that are stored as [value, flag] pairs.

    Args:
      race_data: Dictionary containing race result data
    """
    # Clean up the data by extracting first element from array fields
    cleaned_data = {}
    for key, value in race_data.items():
      if key in self._ARRAY_FIELDS and isinstance(value, list) and len(value) > 0:
        cleaned_data[key] = value[0]
      else:
        cleaned_data[key] = value

    self._data = cleaned_data

  def __getattr__(self, name: str) -> Any:  # noqa: ANN401
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

  def __getitem__(self, key: str) -> Any:  # noqa: ANN401
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
    return f'RaceFinish({items})'

  def __str__(self) -> str:
    """Return human-readable string with all race data.

    Returns:
      Multi-line string showing all fields
    """
    lines = ['RaceFinish(']
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
