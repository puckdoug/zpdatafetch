"""Python object representations for ZwiftPower race sprint data.

This module defines typed Python objects for race sprint data from ZwiftPower's
event_sprints API endpoint. Provides both collection and individual sprint
result classes with attribute access and backwards compatibility.
"""

from typing import Any


# ===============================================================================
class ZPRiderSprint:
  """Represents a single rider's sprint result in a race.

  Provides attribute-based access to sprint result fields from ZwiftPower's
  event_sprints API. Supports both attribute access (obj.field) and dict-style
  access (obj['field']) for backwards compatibility.

  Example:
    rider = ZPRiderSprint({'name': 'John', 'sprint_id': 1, 'distance': 500})
    print(rider.name)  # 'John'
    print(rider['sprint_id'])  # 1
    data = rider.asdict()  # Get original dict
  """

  def __init__(self, rider_data: dict[str, Any] | None = None) -> None:
    """Initialize a rider sprint result.

    Args:
      rider_data: Dictionary containing rider sprint data from API.
                  If None, creates an empty rider sprint object.
    """
    self._data = rider_data if rider_data is not None else {}

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to rider sprint fields.

    Args:
      name: Field name to access

    Returns:
      Field value from sprint data

    Raises:
      AttributeError: If field doesn't exist
    """
    # Prevent infinite recursion for _data and other private attributes
    if name.startswith('_'):
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
      Field value from sprint data
    """
    return self._data[key]

  def __contains__(self, key: str) -> bool:
    """Check if field exists in sprint data.

    Args:
      key: Field name to check

    Returns:
      True if field exists, False otherwise
    """
    return key in self._data

  def asdict(self) -> dict[str, Any]:
    """Return original dictionary representation.

    Provides backwards compatibility with code expecting raw dicts.

    Returns:
      Original sprint data dictionary
    """
    return self._data

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of sprint data
    """
    import json

    return json.dumps(self._data, indent=2)


# ===============================================================================
class ZPRaceSprint:
  """Collection of rider sprint results for a race.

  Provides array-like access to individual rider sprint results from
  ZwiftPower's event_sprints API. Supports iteration, indexing, and slicing.

  The sprint data includes race metadata and a list of rider sprint results.
  Each rider result is wrapped in a ZPRiderSprint object for typed access.

  Example:
    sprint = ZPRaceSprint({'data': [{'name': 'John'}, {'name': 'Jane'}]})
    print(len(sprint))  # 2
    print(sprint[0].name)  # 'John'
    for rider in sprint:
      print(rider.name)
  """

  def __init__(self, sprint_data: dict[str, Any] | None = None) -> None:
    """Initialize a race sprint collection.

    Args:
      sprint_data: Dictionary containing race sprint data from API,
                   including 'data' array of rider sprint results.
                   If None, creates an empty race sprint object.
    """
    self._data = sprint_data if sprint_data is not None else {}

    # Extract rider sprint list
    rider_list = self._data.get('data', [])

    # Create ZPRiderSprint objects for each rider sprint
    self._riders = [ZPRiderSprint(rider_data) for rider_data in rider_list]

  def __len__(self) -> int:
    """Return number of rider sprints.

    Returns:
      Count of rider sprint results
    """
    return len(self._riders)

  def __getitem__(self, index: int | slice) -> 'ZPRiderSprint | list[ZPRiderSprint]':
    """Access rider sprints by index or slice.

    Args:
      index: Integer index or slice object

    Returns:
      Single ZPRiderSprint or list of ZPRiderSprint objects
    """
    return self._riders[index]

  def __iter__(self):
    """Iterate over rider sprints.

    Returns:
      Iterator over ZPRiderSprint objects
    """
    return iter(self._riders)

  def asdict(self) -> dict[str, Any]:
    """Return original dictionary representation.

    Provides backwards compatibility with code expecting raw dicts.

    Returns:
      Original sprint data dictionary
    """
    return self._data

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of rider sprint dictionaries.

    Useful for serialization or backwards compatibility.

    Returns:
      List of rider sprint dictionaries
    """
    return [rider.asdict() for rider in self._riders]

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of sprint data
    """
    import json

    return json.dumps(self._data, indent=2)
