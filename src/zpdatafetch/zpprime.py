"""Python object representations for ZwiftPower race prime data.

This module defines typed Python objects for race prime (sprint/KOM) data from
ZwiftPower's event_primes API endpoint. Primes have a complex nested structure:
race_id -> category -> prime_type -> prime_segments -> rider_results

Each prime segment has metadata (lap, name, id, sprint_id) and multiple
ZPPrimeResult objects representing individual rider performances.
"""

import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any, overload

from zpdatafetch.zp_utils import (
  convert_gender,
  convert_msec_to_iso8601,
  set_rider_category,
)


@dataclass(slots=True)
class ZPPrimeResult:
  """Represents one rider's performance in a prime segment.

  Contains data for a single rider competing in a prime/sprint segment.
  The position (1st, 2nd, etc.) is derived from the rider_N key.
  """

  # Rider identification
  zwift_id: int = 0  # Zwift user ID
  name: str = ''  # Rider name

  # Performance metrics
  position: int = 0  # Position in this segment (1, 2, 3, ...)
  msec: int = 0  # Time in milliseconds since epoch
  finish_timestamp: str = ''  # ISO8601 formatted finish time with milliseconds
  msec_diff: float = 0.0  # Time difference from 1st place
  elapsed: float = 0.0  # Elapsed time in seconds
  elapsed_diff: float = 0.0  # Elapsed time difference from 1st place

  # Rider attributes
  zftp: int = 0  # Functional threshold power
  weight: float = 0.0  # Weight in kg
  age: str = ''  # Age group
  gender: str = ''  # Gender (male/female)
  flag: str = ''  # Country flag code

  # Rankings and skill
  rank: str = ''  # Overall ranking
  skill: int = 0  # Skill rating
  category: str = ''  # Category (A, B, C, D) converted from div

  # Extra fields
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(
    cls,
    data: dict[str, Any],
    position: int = 0,
  ) -> 'ZPPrimeResult':
    """Create instance from rider data dict.

    Args:
      data: Dictionary containing rider performance data
      position: Position number (derived from rider_N key)

    Returns:
      ZPPrimeResult instance with parsed fields
    """
    known_fields = {
      'zwid',
      'name',
      'msec',
      'msec_diff',
      'elapsed',
      'elapsed_diff',
      'ftp',
      'w',
      'age',
      'gender',
      'flag',
      'tid',
      'tname',
      'rank',
      'skill',
      'div',
    }

    # Separate excluded and unknown fields
    excluded = {}
    if 'tid' in data:
      excluded['tid'] = data['tid']
    if 'tname' in data:
      excluded['tname'] = data['tname']

    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    # Convert div to category using utility function
    div = int(data.get('div', 0))
    category = set_rider_category(div)

    msec_value = int(data.get('msec', 0))
    return cls(
      zwift_id=int(data.get('zwid', 0)),
      name=str(data.get('name', '')),
      position=position,
      msec=msec_value,
      finish_timestamp=convert_msec_to_iso8601(msec_value),
      msec_diff=float(data.get('msec_diff', 0.0)),
      elapsed=float(data.get('elapsed', 0.0)),
      elapsed_diff=float(data.get('elapsed_diff', 0.0)),
      zftp=int(data.get('ftp', 0)) if data.get('ftp') else 0,
      weight=float(data.get('w', 0.0)) if data.get('w') else 0.0,
      age=str(data.get('age', '')),
      gender=convert_gender(data.get('gender', '')),
      flag=str(data.get('flag', '')),
      rank=str(data.get('rank', '')),
      skill=int(data.get('skill', 0)),
      category=category,
      _excluded=excluded,
      _extra=extra,
    )

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown/new fields from API response."""
    return dict(self._extra)

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access for backwards compatibility."""
    mapping = {
      'zwid': 'zwift_id',
      'name': 'name',
      'msec': 'msec',
      'msec_diff': 'msec_diff',
      'elapsed': 'elapsed',
      'elapsed_diff': 'elapsed_diff',
      'ftp': 'zftp',
      'w': 'weight',
      'age': 'age',
      'gender': 'gender',
      'flag': 'flag',
      'rank': 'rank',
      'skill': 'skill',
      'div': 'category',
    }
    # Check excluded fields first
    if key in self._excluded:
      return self._excluded[key]
    if key in mapping:
      return getattr(self, mapping[key])
    raise KeyError(key)

  def __contains__(self, key: str) -> bool:
    """Check if field exists."""
    return (
      key
      in {
        'zwid',
        'name',
        'msec',
        'msec_diff',
        'elapsed',
        'elapsed_diff',
        'ftp',
        'w',
        'age',
        'gender',
        'flag',
        'rank',
        'skill',
        'div',
      }
      or key in self._excluded
    )

  def asdict(self) -> dict[str, Any]:
    """Return result data as dictionary with typed field values."""
    from dataclasses import asdict as dataclass_asdict

    result = dataclass_asdict(self)
    result.pop('_excluded', None)
    result.pop('_extra', None)
    return result

  def json(self) -> str:
    """Return JSON representation of result data."""
    return json.dumps(self.asdict(), indent=2)


@dataclass(slots=True)
class ZPPrimeSegment:
  """Represents a prime segment with multiple rider results.

  Contains metadata about the segment (lap, name, id, sprint_id, pen) and
  the ordered list of rider performances (ZPPrimeResult objects).
  """

  # Segment identification
  lap: int = 0  # Lap number
  name: str = ''  # Segment/sprint name
  id: int = 0  # Segment/result id
  sprint_id: int = 0  # Sprint/segment type ID
  pen: str = ''  # Category/pen (A, B, C, D, E) from parent ZPPrime

  # Rider results (ordered by position)
  _results: list[ZPPrimeResult] = field(default_factory=list, repr=False)

  # Extra fields
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any], pen: str = '') -> 'ZPPrimeSegment':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing segment and rider data
      pen: Category/pen (A, B, C, D, E) from parent ZPPrime

    Returns:
      ZPPrimeSegment instance with parsed fields and rider results
    """
    known_fields = {'lap', 'name', 'id', 'sprint_id'}

    # Extract rider data from rider_N keys
    results = []
    for key, value in sorted(data.items()):
      if key.startswith('rider_'):
        position = int(key.split('_')[1])
        if isinstance(value, dict):
          results.append(ZPPrimeResult.from_dict(value, position=position))

    # Find extra fields
    extra = {}
    for key, value in data.items():
      if key not in known_fields and not key.startswith('rider_'):
        extra[key] = value

    return cls(
      lap=int(data.get('lap', 0)),
      name=str(data.get('name', '')),
      id=int(data.get('id', 0)),
      sprint_id=int(data.get('sprint_id', 0)),
      pen=pen,
      _results=results,
      _excluded={},
      _extra=extra,
    )

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown/new fields from API response."""
    return dict(self._extra)

  def __len__(self) -> int:
    """Return number of rider results in this segment."""
    return len(self._results)

  def __getitem__(
    self,
    index: int | slice,
  ) -> ZPPrimeResult | list[ZPPrimeResult]:
    """Get rider result(s) by index or slice."""
    return self._results[index]

  def __iter__(self) -> Iterator[ZPPrimeResult]:
    """Iterate over rider results."""
    return iter(self._results)

  def __contains__(self, key: str) -> bool:
    """Check if field exists."""
    return key in {'lap', 'name', 'id', 'sprint_id'}

  def asdict(self) -> dict[str, Any]:
    """Return segment data as dictionary with typed field values."""
    from dataclasses import asdict as dataclass_asdict

    result = dataclass_asdict(self)
    result.pop('_excluded', None)
    result.pop('_extra', None)
    # Convert _results to list of dicts for serialization
    result['_results'] = [rider.asdict() for rider in self._results]
    return result

  def __repr__(self) -> str:
    """Return detailed representation showing segment info and results.

    Returns:
      String representation with lap, name, pen, and results list
    """
    return (
      f'ZPPrimeSegment(lap={self.lap}, name={self.name!r}, '
      f'pen={self.pen!r}, results={self._results!r})'
    )

  def json(self) -> str:
    """Return JSON representation of segment data."""
    return json.dumps(self.asdict(), indent=2)


@dataclass(slots=True)
class ZPPrime(Sequence):
  """Represents all prime data for a single race.

  Contains prime segments organized by category and prime type.
  The data structure is: category -> prime_type -> list of ZPPrimeSegment objects.

  For a given category (A, B, C, D, E) and prime type (msec/elapsed),
  there are multiple ZPPrimeSegment objects, each representing a prime segment
  with multiple rider performances.

  Implements Sequence protocol to provide array-like access to all segments.
  """

  # Race identification
  race_id: int = 0  # Race ID this prime data belongs to

  # Internal data storage
  _categories: dict[str, dict[str, list[ZPPrimeSegment]]] = field(
    default_factory=dict,
    repr=False,
  )  # category -> prime_type -> segments

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  def __init__(
    self,
    prime_data: dict[str, Any] | None = None,
    *,
    race_id: int = 0,
    _categories: dict[str, dict[str, list[ZPPrimeSegment]]] | None = None,
    _excluded: dict[str, Any] | None = None,
    _extra: dict[str, Any] | None = None,
  ) -> None:
    """Initialize a race prime collection.

    Supports both legacy dict-based initialization and new dataclass pattern.

    Args:
      prime_data: Dictionary containing nested prime data (legacy pattern)
      race_id: Race ID this prime data belongs to
      _categories: Categories dict (from from_dict)
      _excluded: Excluded fields dict (from from_dict)
      _extra: Extra fields dict (from from_dict)
    """
    self.race_id = race_id
    if prime_data is not None:
      # Legacy pattern: ZPPrime(dict)
      temp = ZPPrime.from_dict(prime_data)
      self._categories = temp._categories
      self._excluded = temp._excluded
      self._extra = temp._extra
    else:
      # New dataclass pattern
      self._categories = _categories or {}
      self._excluded = _excluded or {}
      self._extra = _extra or {}

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPPrime':
    """Create instance from API response dict.

    Args:
      data: Dictionary with structure: category -> prime_type -> data array

    Returns:
      ZPPrime instance with segments organized by category and prime type
    """
    # Parse nested structure into typed objects
    categories: dict[str, dict[str, list[ZPPrimeSegment]]] = {}

    for category, cat_data in data.items():
      if not isinstance(cat_data, dict):
        continue

      categories[category] = {}

      for prime_type, type_data in cat_data.items():
        if not isinstance(type_data, dict):
          continue

        # Extract data array and create segment objects
        segment_list = type_data.get('data', [])
        categories[category][prime_type] = [
          ZPPrimeSegment.from_dict(seg_data, pen=category)
          for seg_data in segment_list
          if isinstance(seg_data, dict)
        ]

    return cls(
      _categories=categories,
      _excluded={},
      _extra={},
    )

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown/new fields from API response."""
    return dict(self._extra)

  def __contains__(self, key: object) -> bool:  # type: ignore[override]
    """Check if category exists in prime data (dict-style) or segment exists (sequence)."""
    if isinstance(key, str):
      return key in self._categories
    return False

  # Sequence protocol
  def __len__(self) -> int:
    """Return total number of segments across all categories and prime types."""
    total = 0
    for cat_data in self._categories.values():
      for segment_list in cat_data.values():
        total += len(segment_list)
    return total

  @overload
  def __getitem__(self, index: int) -> ZPPrimeSegment: ...

  @overload
  def __getitem__(self, index: slice) -> list[ZPPrimeSegment]: ...

  @overload
  def __getitem__(self, index: str) -> dict[str, list[ZPPrimeSegment]]: ...

  def __getitem__(
    self,
    index: int | slice | str,
  ) -> ZPPrimeSegment | list[ZPPrimeSegment] | dict[str, list[ZPPrimeSegment]]:
    """Get segment(s) by index/slice (Sequence) or by category (dict-style).

    Supports both Sequence protocol (integer/slice access to all segments)
    and dict-style access by category (for backwards compatibility).

    Args:
      index: Integer index, slice, or category string key (A, B, C, D, E)

    Returns:
      Single/list of ZPPrimeSegment objects (int/slice) or dict (str key)
    """
    # Dict-style access by category string (A, B, C, D, E)
    if isinstance(index, str):
      return self._categories.get(index, {})
    # Sequence-style access - flatten all segments and index by int/slice
    all_segments = self.get_all_segments()
    return all_segments[index]

  def __iter__(self) -> Iterator[ZPPrimeSegment]:
    """Iterate over all segments across all categories and prime types."""
    return iter(self.get_all_segments())

  def get_segments(
    self,
    category: str,
    prime_type: str,
  ) -> list[ZPPrimeSegment]:
    """Get typed segment objects for a category and prime type.

    Args:
      category: Category key (e.g., 'A', 'B', 'C', 'D', 'E')
      prime_type: Prime type ('msec' or 'elapsed')

    Returns:
      List of ZPPrimeSegment objects for the category/type
    """
    return self._categories.get(category, {}).get(prime_type, [])

  def get_all_segments(self) -> list[ZPPrimeSegment]:
    """Get all segments across all categories and prime types.

    Returns:
      Flat list of all ZPPrimeSegment objects
    """
    all_segments: list[ZPPrimeSegment] = []
    for cat_data in self._categories.values():
      for segment_list in cat_data.values():
        all_segments.extend(segment_list)
    return all_segments

  @property
  def segments(self) -> list[ZPPrimeSegment]:
    """Get all segments as a flat list.

    Convenience property for accessing all segments across all categories
    and prime types as a single flat list.

    Returns:
      Flat list of all ZPPrimeSegment objects
    """
    return self.get_all_segments()

  def __repr__(self) -> str:
    """Return detailed representation showing race_id and segments.

    Returns:
      String representation with race_id and full segments list
    """
    segments_list = self.get_all_segments()
    return f'ZPPrime(race_id={self.race_id}, segments={segments_list!r})'

  def asdict(self) -> dict[str, Any]:
    """Return prime data as dictionary with typed field values.

    Returns:
      Dict with race_id and nested _categories structure
    """
    # Serialize nested structure manually since it contains custom objects
    categories_dict = {}
    for category, cat_data in self._categories.items():
      categories_dict[category] = {}
      for prime_type, segments in cat_data.items():
        categories_dict[category][prime_type] = [seg.asdict() for seg in segments]

    return {
      'race_id': self.race_id,
      '_categories': categories_dict,
    }

  def json(self) -> str:
    """Return JSON string representation."""
    return json.dumps(self.asdict(), indent=2)
