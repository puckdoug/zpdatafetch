"""Represents race signup data from Zwiftpower."""

import json
from typing import Any


class ZPRiderSignup:
  """Represents a single rider's signup for a race.

  Wraps individual rider signup data with convenient attribute access.

  Attributes:
    All rider signup fields are accessible as attributes, including:
    - zwid: Rider's Zwift ID
    - name: Rider's name
    - category: Registration category
    - And all other fields from the rider signup data
  """

  def __init__(self, rider_data: dict[str, Any] | None = None) -> None:
    """Initialize a ZPRiderSignup from rider signup dictionary.

    Args:
      rider_data: Dictionary containing rider signup data.
                  If None, creates an empty rider signup object.
    """
    self._data = rider_data if rider_data is not None else {}

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to rider signup fields."""
    if name.startswith("_"):
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    try:
      return self._data[name]
    except KeyError:
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to rider signup data."""
    return self._data[key]

  def __repr__(self) -> str:
    """Return detailed representation showing all rider signup data."""
    items = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
    return f"ZPRiderSignup({items})"

  def __str__(self) -> str:
    """Return human-readable string with all rider signup data."""
    lines = ["ZPRiderSignup("]
    for key, value in self._data.items():
      lines.append(f"  {key}={value!r},")
    lines.append(")")
    return "\n".join(lines)

  def asdict(self) -> dict[str, Any]:
    """Return the underlying rider signup data as a dictionary."""
    return self._data

  def json(self) -> str:
    """Return JSON representation of rider signup data."""
    return json.dumps(self._data, indent=2)


class ZPRaceSignup:
  """Collection of rider signups for a race.

  Wraps race signup data with array-like access to individual rider signups.
  Provides convenient iteration and indexing operations.

  Attributes:
    All race-level fields are accessible as attributes
    Access individual rider signups via indexing: signup[0], signup[1], etc.
  """

  def __init__(self, signup_data: dict[str, Any] | None = None) -> None:
    """Initialize a ZPRaceSignup from signup data dictionary.

    Args:
      signup_data: Dictionary containing race signup data.
                   If None, creates an empty race signup object.
    """
    self._data = signup_data if signup_data is not None else {}

    # Create list of rider signup objects from 'data' array
    rider_list = self._data.get("data", [])
    self._riders = [ZPRiderSignup(rider_data) for rider_data in rider_list]

  def __len__(self) -> int:
    """Return the number of riders signed up."""
    return len(self._riders)

  def __getitem__(self, index: int | slice) -> ZPRiderSignup | list[ZPRiderSignup]:
    """Access rider signups by index or slice."""
    return self._riders[index]

  def __iter__(self):
    """Iterate over rider signups."""
    return iter(self._riders)

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to race-level signup fields."""
    if name.startswith("_"):
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    try:
      return self._data[name]
    except KeyError:
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

  def __repr__(self) -> str:
    """Return detailed representation."""
    return f"ZPRaceSignup(riders={len(self._riders)})"

  def __str__(self) -> str:
    """Return human-readable string."""
    return f"ZPRaceSignup with {len(self._riders)} riders signed up"

  def asdict(self) -> dict[str, Any]:
    """Return the underlying signup data as a dictionary."""
    return self._data

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of rider signups as dictionaries."""
    return [rider.asdict() for rider in self._riders]

  def json(self) -> str:
    """Return JSON representation of signup data."""
    return json.dumps(self._data, indent=2)
