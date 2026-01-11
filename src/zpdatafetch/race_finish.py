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

  def __init__(self, race_data: dict[str, Any]) -> None:
    """Initialize a RaceFinish from race data dictionary.

    Args:
      race_data: Dictionary containing race result data
    """
    self._data = race_data

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
    """Return string representation."""
    event_title = self._data.get('event_title', 'Unknown')
    pos = self._data.get('pos', '?')
    return f"RaceFinish(event='{event_title}', pos={pos})"

  def asdict(self) -> dict[str, Any]:
    """Return the underlying race data as a dictionary.

    Returns:
      Dictionary containing all race data
    """
    return self._data
