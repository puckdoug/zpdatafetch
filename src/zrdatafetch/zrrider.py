"""Pure dataclass for Zwiftracing rider data.

This module provides the ZRRider dataclass for representing rider
rating data without any fetch logic. Fetching is handled by ZRRiderFetch.
"""

from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr_utils import (
  extract_nested_value,
  safe_float,
  safe_int,
  safe_str,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class ZRRider:
  """Rider rating data from Zwiftracing API.

  Represents a rider's current and historical ratings across multiple
  timeframes (current, max30, max90).

  This is a pure data container with no fetch logic.

  Attributes:
    zwift_id: Rider's Zwift ID
    name: Rider's display name
    gender: Rider's gender (M/F)
    current_rating: Current rating score
    current_rank: Current category rank
    max30_rating: Maximum rating in last 30 days
    max30_rank: Max30 category rank
    max90_rating: Maximum rating in last 90 days
    max90_rank: Max90 category rank
    zrcs: Zwiftracing compound score
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
  """

  # Public attributes
  zwift_id: int = 0
  name: str = 'Nobody'
  gender: str = 'M'
  current_rating: float = 0.0
  current_rank: str = 'Unranked'
  max30_rating: float = 0.0
  max30_rank: str = 'Unranked'
  max90_rating: float = 0.0
  max90_rank: str = 'Unranked'
  zrcs: float = 0.0

  # Field classification
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRRider':
    """Create instance from API response dict.

    Parses Zwiftracing API response and extracts rider rating fields.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing rider data from API

    Returns:
      ZRRider instance with parsed fields
    """
    # Known fields that will be extracted
    known_fields = {
      'name',
      'gender',
      'race',
      'power',
      'riderId',
      'zwiftId',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded: set[str] = set()

    # Check for error in response
    if 'message' in data:
      logger.error(f'API error in rider data: {data["message"]}')
      return cls()

    # Check for required fields
    if 'name' not in data or 'race' not in data:
      logger.warning('Missing required fields (name or race) in response')
      return cls()

    try:
      # Extract using safe utilities
      name = safe_str(data.get('name'), default='Nobody')
      gender = safe_str(data.get('gender'), default='M')

      # ZRCS (compound score)
      zrcs = safe_float(extract_nested_value(data, 'power', 'compoundScore'))

      # Current rating
      current_rating = safe_float(
        extract_nested_value(data, 'race', 'current', 'rating'),
      )
      current_rank = safe_str(
        extract_nested_value(data, 'race', 'current', 'mixed', 'category'),
        default='Unranked',
      )

      # Max90 rating
      max90_rating = safe_float(
        extract_nested_value(data, 'race', 'max90', 'rating'),
      )
      max90_rank = safe_str(
        extract_nested_value(data, 'race', 'max90', 'mixed', 'category'),
        default='Unranked',
      )

      # Max30 rating
      max30_rating = safe_float(
        extract_nested_value(data, 'race', 'max30', 'rating'),
      )
      max30_rank = safe_str(
        extract_nested_value(data, 'race', 'max30', 'mixed', 'category'),
        default='Unranked',
      )

      # Extract zwift_id (try multiple possible field names)
      zwift_id = safe_int(data.get('riderId', data.get('zwiftId')))

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
        zwift_id=zwift_id,
        name=name,
        gender=gender,
        current_rating=current_rating,
        current_rank=current_rank,
        max30_rating=max30_rating,
        max30_rank=max30_rank,
        max90_rating=max90_rating,
        max90_rank=max90_rank,
        zrcs=zrcs,
        _excluded=excluded,
        _extra=extra,
      )

    except (KeyError, TypeError, ValueError) as e:
      logger.error(f'Error parsing rider rating data: {e}')
      return cls()

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
    """Return all excluded fields recognized but not explicitly handled.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields captured from API response.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)
