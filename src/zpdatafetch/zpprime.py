"""Python object representations for ZwiftPower race prime data.

This module defines typed Python objects for race prime (sprint/KOM) data from
ZwiftPower's event_primes API endpoint. Primes have a complex nested structure:
race_id -> category -> prime_type -> data.
"""

from typing import Any


# ===============================================================================
class ZPPrimeSegment:
  """Represents a single prime segment result.

  Provides attribute-based access to prime segment fields from ZwiftPower's
  event_primes API. Supports both attribute access (obj.field) and dict-style
  access (obj['field']) for backwards compatibility.

  Example:
    segment = ZPPrimeSegment({'sprint_id': 1, 'name': 'Sprint 1', 'position': 1})
    print(segment.name)  # 'Sprint 1'
    print(segment['position'])  # 1
    data = segment.asdict()  # Get original dict
  """

  def __init__(self, segment_data: dict[str, Any]) -> None:
    """Initialize a prime segment.

    Args:
      segment_data: Dictionary containing prime segment data from API
    """
    self._data = segment_data

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to prime segment fields.

    Args:
      name: Field name to access

    Returns:
      Field value from segment data

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
      Field value from segment data
    """
    return self._data[key]

  def __contains__(self, key: str) -> bool:
    """Check if field exists in segment data.

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
      Original segment data dictionary
    """
    return self._data

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of segment data
    """
    import json

    return json.dumps(self._data, indent=2)


# ===============================================================================
class ZPPrime:
  """Complex nested structure for race prime data.

  Represents prime data for a single race with the structure:
  category -> prime_type -> data array

  The data is organized by category (A, B, C, D, E) and prime type
  (msec for fastest absolute lap, elapsed for first to sprint).
  Each category/type combination contains a list of ZPPrimeSegment objects.

  Example:
    prime = ZPPrime({
      'A': {
        'msec': {'data': [{'sprint_id': 1, 'name': 'Sprint 1'}]},
        'elapsed': {'data': []},
      },
    })
    print(prime['A']['msec']['data'])  # Access via dict-style
    segments = prime.get_segments('A', 'msec')  # Get ZPPrimeSegment objects
  """

  def __init__(self, prime_data: dict[str, Any]) -> None:
    """Initialize a race prime collection.

    Args:
      prime_data: Dictionary containing nested prime data from API,
                  structured as category -> prime_type -> data
    """
    self._data = prime_data

    # Pre-parse all segments into objects for convenient access
    self._segments: dict[str, dict[str, list[ZPPrimeSegment]]] = {}

    for category, cat_data in prime_data.items():
      if not isinstance(cat_data, dict):
        continue

      self._segments[category] = {}

      for prime_type, type_data in cat_data.items():
        if not isinstance(type_data, dict):
          continue

        # Extract data array and create segment objects
        segment_list = type_data.get('data', [])
        self._segments[category][prime_type] = [
          ZPPrimeSegment(seg_data)
          for seg_data in segment_list
          if isinstance(seg_data, dict)
        ]

  def __getitem__(self, key: str) -> Any:
    """Allow dict-style access for backwards compatibility.

    Args:
      key: Category key (e.g., 'A', 'B', 'C', 'D', 'E')

    Returns:
      Nested dictionary for the category
    """
    return self._data[key]

  def __contains__(self, key: str) -> bool:
    """Check if category exists in prime data.

    Args:
      key: Category key to check

    Returns:
      True if category exists, False otherwise
    """
    return key in self._data

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
    return self._segments.get(category, {}).get(prime_type, [])

  def get_all_segments(self) -> list[ZPPrimeSegment]:
    """Get all segments across all categories and prime types.

    Returns:
      Flat list of all ZPPrimeSegment objects
    """
    all_segments: list[ZPPrimeSegment] = []
    for cat_segments in self._segments.values():
      for seg_list in cat_segments.values():
        all_segments.extend(seg_list)
    return all_segments

  def asdict(self) -> dict[str, Any]:
    """Return original dictionary representation.

    Provides backwards compatibility with code expecting raw dicts.

    Returns:
      Original prime data dictionary
    """
    return self._data

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of prime data
    """
    import json

    return json.dumps(self._data, indent=2)
