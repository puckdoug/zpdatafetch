"""Pure dataclasses for Zwiftracing race result data.

This module provides dataclasses for representing race results without
any fetch logic. Fetching is handled by ZRResultFetch.
"""

from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr_utils import safe_float, safe_int, safe_str

logger = get_logger(__name__)


@dataclass(slots=True)
class ZRRiderResult:
  """Individual rider result from a Zwiftracing race.

  Represents a single rider's performance and rating change in a race result.

  Attributes:
    zwift_id: Rider's Zwift ID
    position: Finishing position in the race
    position_in_category: Position within their category
    category: Category (e.g., A, B, C, D)
    time: Finish time in seconds (for timed races)
    gap: Time gap from first place in seconds
    rating_before: Rating before the race
    rating: Rating after the race
    rating_delta: Change in rating from the race
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
  """

  zwift_id: int = 0
  position: int = 0
  position_in_category: int = 0
  category: str = ''
  time: float = 0.0
  gap: float = 0.0
  rating_before: float = 0.0
  rating: float = 0.0
  rating_delta: float = 0.0

  # Field classification
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRRiderResult':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing rider result data

    Returns:
      ZRRiderResult instance with parsed fields
    """
    known_fields = {
      'riderId',
      'position',
      'positionInCategory',
      'category',
      'time',
      'gap',
      'ratingBefore',
      'rating',
      'ratingDelta',
    }

    recognized_but_excluded: set[str] = set()

    # Classify remaining fields
    excluded = {}
    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        if key in recognized_but_excluded:
          excluded[key] = value
        else:
          extra[key] = value

    return cls(
      zwift_id=safe_int(data.get('riderId')),
      position=safe_int(data.get('position')),
      position_in_category=safe_int(data.get('positionInCategory')),
      category=safe_str(data.get('category')),
      time=safe_float(data.get('time')),
      gap=safe_float(data.get('gap')),
      rating_before=safe_float(data.get('ratingBefore')),
      rating=safe_float(data.get('rating')),
      rating_delta=safe_float(data.get('ratingDelta')),
      _excluded=excluded,
      _extra=extra,
    )

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with all public attributes
    """
    result = asdict(self)
    result.pop('_extra', None)
    result.pop('_excluded', None)
    return result

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)


@dataclass(slots=True)
class ZRRaceResult(Sequence):
  """Race result data from Zwiftracing API.

  Represents all rider results from a specific race, including race metadata.
  Implements Sequence protocol for accessing individual rider results.

  Attributes:
    race_id: The race ID (Zwift event ID)
    event_title: Race event title
    event_time: Unix timestamp of event
    route_id: Zwift route ID
    distance: Race distance
    race_type: Type of race (e.g., "Race")
    race_subtype: Subtype (e.g., "Points")
    _results: List of ZRRiderResult objects (internal)
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
  """

  # Public metadata fields
  race_id: int = 0
  event_title: str = ''
  event_time: int = 0
  route_id: str = ''
  distance: float = 0.0
  race_type: str = ''
  race_subtype: str = ''

  # Collection of rider results (private)
  _results: list[ZRRiderResult] = field(
    default_factory=list,
    repr=False,
    init=False,
  )

  # Field classification
  _excluded: dict[str, Any] = field(
    default_factory=dict,
    repr=False,
    init=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict,
    repr=False,
    init=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRRaceResult':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing race result data

    Returns:
      ZRRaceResult instance with parsed fields and results
    """
    known_fields = {
      'eventId',
      'time',
      'routeId',
      'distance',
      'title',
      'type',
      'subType',
      'results',
    }

    recognized_but_excluded: set[str] = set()

    # Parse rider results
    results_data = data.get('results', [])
    results = [ZRRiderResult.from_dict(r) for r in results_data]

    # Classify remaining fields
    excluded = {}
    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        if key in recognized_but_excluded:
          excluded[key] = value
        else:
          extra[key] = value

    # Create instance using safe utilities
    instance = cls(
      race_id=safe_int(data.get('eventId')),
      event_title=safe_str(data.get('title')),
      event_time=safe_int(data.get('time')),
      route_id=safe_str(data.get('routeId')),
      distance=safe_float(data.get('distance')),
      race_type=safe_str(data.get('type')),
      race_subtype=safe_str(data.get('subType')),
    )

    # Set internal fields
    instance._results = results
    instance._excluded = excluded
    instance._extra = extra

    return instance

  # Sequence protocol implementation
  def __len__(self) -> int:
    """Return the number of rider results.

    Returns:
      Number of riders
    """
    return len(self._results)

  def __getitem__(self, index: int) -> ZRRiderResult:  # type: ignore[override]
    """Access rider result by index.

    Args:
      index: Integer index

    Returns:
      ZRRiderResult object

    Raises:
      IndexError: If index out of range
    """
    return self._results[index]

  def __iter__(self) -> Iterator[ZRRiderResult]:
    """Iterate over rider results.

    Returns:
      Iterator over ZRRiderResult objects
    """
    return iter(self._results)

  def __repr__(self) -> str:
    """Return detailed representation.

    Returns:
      String showing metadata and rider count
    """
    return (
      f'ZRRaceResult(race_id={self.race_id}, event_title={self.event_title!r}, '
      f'results={len(self._results)})'
    )

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with race metadata and results
    """
    return {
      'race_id': self.race_id,
      'event_title': self.event_title,
      'event_time': self.event_time,
      'route_id': self.route_id,
      'distance': self.distance,
      'race_type': self.race_type,
      'race_subtype': self.race_subtype,
      'results': [r.asdict() for r in self._results],
    }

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)
