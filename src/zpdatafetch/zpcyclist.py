"""Python object representation for ZwiftPower cyclist profile data.

This module defines a typed Python object for cyclist profile data from
ZwiftPower's profile API endpoint. Wraps profile data and provides access
to the cyclist's race log via ZPRacelog.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from zpdatafetch.zpracelog import ZPRacelog


# ===============================================================================
@dataclass(slots=True)
class ZPCyclist:
  """Represents a cyclist's profile and race history from ZwiftPower.

  Provides attribute-based access to profile fields from ZwiftPower's profile
  API. The profile includes demographics, performance metrics, and race history.

  The race history is accessible via the `racelog` property, which returns a
  ZPRacelog object containing ZPRaceFinish objects for each race.

  Attributes:
    _data: Original API response dictionary (for backwards compatibility)
    _excluded: Recognized but not yet explicit fields
    _extra: Truly unknown fields from API
    _racelog: Cached ZPRacelog instance (lazy-loaded)

  Example:
    cyclist = ZPCyclist.from_dict({'zwid': 123, 'name': 'John', 'data': [...]})
    print(cyclist.zwift_id)  # 123
    print(cyclist.name)  # 'John'
    racelog = cyclist.racelog  # Get ZPRacelog object
    for race in racelog:
      print(race.position)
  """

  # Original API data (for backwards compatibility and raw access)
  _data: dict[str, Any] = field(default_factory=dict, repr=False)

  # Recognized but not yet explicit fields
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Truly unknown fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  # Cached racelog (not in repr)
  _racelog: ZPRacelog | None = field(default=None, repr=False, init=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "ZPCyclist":
    """Create a ZPCyclist from API response dictionary.

    Separates known fields, recognized-but-unhandled fields, and truly unknown
    fields for proper classification.

    Args:
      data: Dictionary containing cyclist profile data from API

    Returns:
      New ZPCyclist instance with properly classified fields
    """
    # Fields we plan to eventually promote to explicit typed attributes
    # These are documented in the API but not yet handled natively
    recognized_but_excluded = {
      "zwid",  # Will become zwift_id
      "name",  # Will become name field
      "data",  # Will become race data
    }

    excluded = {}
    extra = {}

    for key, value in data.items():
      if key not in recognized_but_excluded:
        # For now, all other fields go to extra since cyclist is mostly a wrapper
        extra[key] = value

    return cls(
      _data=data,
      _excluded=excluded,
      _extra=extra,
    )

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

  def __repr__(self) -> str:
    """Return representation showing cyclist name and zwift_id if available.

    Returns:
      String representation like: ZPCyclist(name='John', zwift_id=123)
    """
    # First check if data is in the response
    if (
      'data' in self._data
      and isinstance(self._data['data'], list)
      and self._data['data']
    ):
      # Profile data is in the first element of the data array
      profile = self._data["data"][0]
      name = profile.get("name", "")
      zwid = profile.get("zwid", "")
      if name or zwid:
        return f"ZPCyclist(name={name!r}, zwift_id={zwid!r})"

    # Fallback: check if profile data is at top level
    name = self._data.get("name", "")
    zwid = self._data.get("zwid", "")
    if name or zwid:
      return f"ZPCyclist(name={name!r}, zwift_id={zwid!r})"

    return "ZPCyclist()"

  @property
  def racelog(self) -> ZPRacelog:
    """Get the cyclist's race history as a ZPRacelog object.

    Lazy-loads the racelog from the 'data' array on first access.

    Returns:
      ZPRacelog object containing ZPRaceFinish objects for each race

    Raises:
      KeyError: If 'data' field is missing from profile

    Example:
      cyclist = ZPCyclist.from_dict({'data': [...]})
      racelog = cyclist.racelog
      for race in racelog:
        print(f"Position {race.position}")
    """
    if self._racelog is None:
      if "data" not in self._data:
        raise KeyError(
          'Cyclist profile missing "data" field. Cannot create racelog.',
        )
      self._racelog = ZPRacelog.from_dict(self._data["data"])
    return self._racelog

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields.

    These are fields documented in the API but not yet promoted to
    explicit typed attributes in the dataclass.

    Returns:
      Dictionary of recognized but unhandled fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields from API response.

    These fields are not yet recognized by the application,
    likely from recent API changes.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)

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
    return json.dumps(self._data, indent=2)
