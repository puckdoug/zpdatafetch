"""Python object representation for ZwiftPower cyclist profile data.

This module defines a typed Python object for cyclist profile data from
ZwiftPower's profile API endpoint. Wraps profile data and provides access
to the cyclist's race log via ZPRacelog.
"""

from typing import Any

from zpdatafetch.zpracelog import ZPRacelog


# ===============================================================================
class ZPCyclist:
  """Represents a cyclist's profile and race history from ZwiftPower.

  Provides attribute-based access to profile fields from ZwiftPower's profile
  API. The profile includes demographics, performance metrics, and race history.
  Supports both attribute access (obj.field) and dict-style access (obj['field'])
  for backwards compatibility.

  The race history is accessible via the `racelog` property, which returns a
  ZPRacelog object containing ZPRaceFinish objects for each race.

  Example:
    cyclist = ZPCyclist({'zwid': 123, 'name': 'John', 'data': [...]})
    print(cyclist.name)  # 'John'
    print(cyclist['zwid'])  # 123
    racelog = cyclist.racelog  # Get ZPRacelog object
    for race in racelog:
      print(race.event_title)
  """

  def __init__(self, cyclist_data: dict[str, Any] | None = None) -> None:
    """Initialize a cyclist profile.

    Args:
      cyclist_data: Dictionary containing cyclist profile data from API,
                    including 'data' array with race history. If None,
                    creates an empty cyclist object.
    """
    self._data = cyclist_data if cyclist_data is not None else {}

    # Create lazy-loaded racelog from data array
    self._racelog: ZPRacelog | None = None

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to cyclist profile fields.

    Args:
      name: Field name to access

    Returns:
      Field value from cyclist data

    Raises:
      AttributeError: If field doesn't exist
    """
    # Prevent infinite recursion for _data and other private attributes
    if name.startswith("_"):
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      )

    try:
      return self._data[name]
    except KeyError as e:
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      ) from e

  def __getitem__(self, key: str) -> Any:
    """Allow dict-style access for backwards compatibility.

    Args:
      key: Field name to access

    Returns:
      Field value from cyclist data
    """
    return self._data[key]

  def __contains__(self, key: str) -> bool:
    """Check if field exists in cyclist data.

    Args:
      key: Field name to check

    Returns:
      True if field exists, False otherwise
    """
    return key in self._data

  @property
  def racelog(self) -> ZPRacelog:
    """Get the cyclist's race history as a ZPRacelog object.

    Lazy-loads the racelog from the 'data' array on first access.

    Returns:
      ZPRacelog object containing ZPRaceFinish objects for each race

    Raises:
      KeyError: If 'data' field is missing from profile

    Example:
      cyclist = ZPCyclist({'data': [...]})
      racelog = cyclist.racelog
      for race in racelog:
        print(f"{race.event_title}: Position {race.pos}")
    """
    if self._racelog is None:
      if "data" not in self._data:
        raise KeyError(
          "Cyclist profile missing 'data' field. Cannot create racelog.",
        )
      self._racelog = ZPRacelog(self._data["data"])
    return self._racelog

  def asdict(self) -> dict[str, Any]:
    """Return original dictionary representation.

    Provides backwards compatibility with code expecting raw dicts.

    Returns:
      Original cyclist profile dictionary
    """
    return self._data

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of cyclist profile data
    """
    import json

    return json.dumps(self._data, indent=2)
