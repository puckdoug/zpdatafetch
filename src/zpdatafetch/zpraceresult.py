"""Represents race result data from Zwiftpower."""

import json
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ZPRiderFinish:
  """Represents a single rider's finish in a race result.

  Uses explicit typed fields for known API data with _extra dict
  to capture unexpected fields for forward compatibility.

  Attributes:
    position: Rider's finishing position
    name: Rider's name
    zwift_id: Rider's Zwift ID
    team: Rider's team name
    time_ms: Finish time in milliseconds
    avg_power: Average power in watts
    avg_wkg: Average power per kg
    avg_hr: Average heart rate
    weight_kg: Rider's weight in kg
    category: Race category
    points: Points awarded
    speed: Average speed
    _extra: Captures unknown fields from API for forward compatibility
  """

  # Explicit typed fields for known API data
  position: int = 0
  name: str = ""
  zwift_id: int = 0
  team: str | None = None
  time_ms: int = 0
  avg_power: float = 0.0
  avg_wkg: float = 0.0
  avg_hr: int = 0
  weight_kg: float = 0.0
  category: str = ""
  points: int = 0
  speed: float = 0.0

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "ZPRiderFinish":
    """Create instance from API response dict.

    Known fields are extracted with type coercion.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing rider result data

    Returns:
      ZPRiderFinish instance with parsed fields
    """
    known_fields = {
      "position",
      "name",
      "zwift_id",
      "team",
      "time_ms",
      "avg_power",
      "avg_wkg",
      "avg_hr",
      "weight_kg",
      "category",
      "points",
      "speed",
    }
    return cls(
      position=int(data.get("position", 0)),
      name=str(data.get("name", "")),
      zwift_id=int(data.get("zwift_id", 0)),
      team=data.get("team"),
      time_ms=int(data.get("time_ms", 0)),
      avg_power=float(data.get("avg_power", 0.0)),
      avg_wkg=float(data.get("avg_wkg", 0.0)),
      avg_hr=int(data.get("avg_hr", 0)),
      weight_kg=float(data.get("weight_kg", 0.0)),
      category=str(data.get("category", "")),
      points=int(data.get("points", 0)),
      speed=float(data.get("speed", 0.0)),
      _extra={k: v for k, v in data.items() if k not in known_fields},
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
      True if field exists
    """
    return hasattr(self, key)

  def asdict(self) -> dict[str, Any]:
    """Return the rider result data as a dictionary.

    Includes all explicit fields and unknown fields from _extra.

    Returns:
      Dictionary containing all rider data
    """
    result = asdict(self)
    extras = result.pop("_extra", {})
    result.update(extras)
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
  event_name: str = ""
  event_date: str = ""

  # Collection of riders (not in __init__, set via from_dict)
  _riders: list[ZPRiderFinish] = field(
    default_factory=list,
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
  def from_dict(cls, data: dict[str, Any]) -> "ZPRaceResult":
    """Create instance from API response dict.

    Parses nested rider data and captures unknown fields.

    Args:
      data: Dictionary containing race result data

    Returns:
      ZPRaceResult instance with parsed fields and riders
    """
    known_fields = {"race_id", "event_name", "event_date", "data"}

    # Parse rider list from nested "data" key
    riders = [ZPRiderFinish.from_dict(r) for r in data.get("data", [])]

    # Create instance with metadata
    instance = cls(
      race_id=int(data.get("race_id", 0)),
      event_name=str(data.get("event_name", "")),
      event_date=str(data.get("event_date", "")),
    )

    # Set riders and extras (not in __init__)
    instance._riders = riders
    instance._extra = {k: v for k, v in data.items() if k not in known_fields}

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
      f"ZPRaceResult(race_id={self.race_id}, event_name={self.event_name!r}, "
      f"event_date={self.event_date!r}, riders={len(self._riders)})"
    )

  def __str__(self) -> str:
    """Return human-readable string.

    Returns:
      String with race info and rider count
    """
    return f"ZPRaceResult with {len(self._riders)} riders"

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
    if name.startswith("_"):
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

  def asdict(self) -> dict[str, Any]:
    """Return the result data as a dictionary.

    Reconstructs dict with all metadata fields and rider data array.

    Returns:
      Dictionary containing race metadata and riders
    """
    return {
      "race_id": self.race_id,
      "event_name": self.event_name,
      "event_date": self.event_date,
      "data": [rider.asdict() for rider in self._riders],
      **self._extra,
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
