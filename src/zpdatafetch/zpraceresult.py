"""Represents race result data from Zwiftpower."""

import json
from typing import Any


class ZPRiderFinish:
  """Represents a single rider's finish in a race result.

  Wraps individual rider result data with convenient attribute access.

  Attributes:
    All rider result fields are accessible as attributes, including:
    - position: Rider's finishing position
    - name: Rider's name
    - time: Finish time
    - And all other fields from the rider result data
  """

  def __init__(self, rider_data: dict[str, Any] | None = None) -> None:
    """Initialize a ZPRiderFinish from rider result dictionary.

    Args:
      rider_data: Dictionary containing rider result data.
                  If None, creates an empty rider finish object.
    """
    self._data = rider_data if rider_data is not None else {}

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to rider result fields."""
    if name.startswith('_'):
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    try:
      return self._data[name]
    except KeyError:
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to rider result data."""
    return self._data[key]

  def __repr__(self) -> str:
    """Return detailed representation showing all rider result data."""
    items = ', '.join(f'{k}={v!r}' for k, v in self._data.items())
    return f'ZPRiderFinish({items})'

  def __str__(self) -> str:
    """Return human-readable string with all rider result data."""
    lines = ['ZPRiderFinish(']
    for key, value in self._data.items():
      lines.append(f'  {key}={value!r},')
    lines.append(')')
    return '\n'.join(lines)

  def asdict(self) -> dict[str, Any]:
    """Return the underlying rider result data as a dictionary."""
    return self._data

  def json(self) -> str:
    """Return JSON representation of rider result data."""
    return json.dumps(self._data, indent=2)


class ZPRaceResult:
  """Collection of rider finishes for a race.

  Wraps race result data with array-like access to individual rider finishes.
  Provides convenient iteration and indexing operations.

  Attributes:
    All race-level fields are accessible as attributes
    Access individual rider results via indexing: result[0], result[1], etc.
  """

  def __init__(self, result_data: dict[str, Any] | None = None) -> None:
    """Initialize a ZPRaceResult from result data dictionary.

    Args:
      result_data: Dictionary containing race result data.
                   If None, creates an empty race result object.
    """
    self._data = result_data if result_data is not None else {}

    # Create list of rider finish objects from 'data' array
    rider_list = self._data.get('data', [])
    self._riders = [ZPRiderFinish(rider_data) for rider_data in rider_list]

  def __len__(self) -> int:
    """Return the number of riders in the result."""
    return len(self._riders)

  def __getitem__(self, index: int | slice) -> ZPRiderFinish | list[ZPRiderFinish]:
    """Access rider finishes by index or slice."""
    return self._riders[index]

  def __iter__(self):
    """Iterate over rider finishes."""
    return iter(self._riders)

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to race-level result fields."""
    if name.startswith('_'):
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    try:
      return self._data[name]
    except KeyError:
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

  def __repr__(self) -> str:
    """Return detailed representation."""
    return f'ZPRaceResult(riders={len(self._riders)})'

  def __str__(self) -> str:
    """Return human-readable string."""
    return f'ZPRaceResult with {len(self._riders)} riders'

  def asdict(self) -> dict[str, Any]:
    """Return the underlying result data as a dictionary."""
    return self._data

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of rider results as dictionaries."""
    return [rider.asdict() for rider in self._riders]

  def json(self) -> str:
    """Return JSON representation of result data."""
    return json.dumps(self._data, indent=2)
