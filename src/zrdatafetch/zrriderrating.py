"""Pure dataclass for Zwiftracing rider rating data.

This module provides the ZRRiderRating dataclass for representing rider
rating data without any fetch logic. Fetching is handled by ZRRiderFetch.
"""

from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ZRRiderRating:
  """Rider rating data from Zwiftracing API.

  Represents a rider's current and historical ratings across multiple
  timeframes (current, max30, max90) as well as derived rating score (DRS).

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
    drs_rating: Derived rating score
    drs_rank: DRS category rank
    zrcs: Zwiftracing compound score
    source: Source of DRS (max30, max90, or none)
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
  drs_rating: float = 0.0
  drs_rank: str = 'Unranked'
  zrcs: float = 0.0
  source: str = 'none'

  # Field classification
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRRiderRating':
    """Create instance from API response dict.

    Parses Zwiftracing API response and extracts rider rating fields.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing rider data from API

    Returns:
      ZRRiderRating instance with parsed fields
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
      name = data.get('name', 'Nobody')
      gender = data.get('gender', 'M')

      # ZRCS (compound score)
      power = data.get('power', {})
      zrcs = power.get('compoundScore', 0.0)

      # Current rating
      race = data.get('race', {})
      current = race.get('current', {})
      current_rating = current.get('rating', 0.0)
      current_mixed = current.get('mixed', {})
      current_rank = current_mixed.get('category', 'Unranked')

      # Max90 rating
      max90 = race.get('max90', {})
      max90_rating_val = max90.get('rating')
      max90_rating = max90_rating_val if max90_rating_val is not None else 0.0
      max90_mixed = max90.get('mixed', {})
      max90_rank = max90_mixed.get('category', 'Unranked')

      # Max30 rating
      max30 = race.get('max30', {})
      max30_rating_val = max30.get('rating')
      max30_rating = max30_rating_val if max30_rating_val is not None else 0.0
      max30_mixed = max30.get('mixed', {})
      max30_rank = max30_mixed.get('category', 'Unranked')

      # Determine DRS (derived rating score)
      drs_rating = 0.0
      drs_rank = 'Unranked'
      source = 'none'

      if max30_rank != 'Unranked':
        drs_rating = max30_rating
        drs_rank = max30_rank
        source = 'max30'
      elif max90_rank != 'Unranked':
        drs_rating = max90_rating
        drs_rank = max90_rank
        source = 'max90'

      # Extract zwift_id (try multiple possible field names)
      zwift_id = data.get('riderId', data.get('zwiftId', 0))

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
        zwift_id=int(zwift_id),
        name=str(name),
        gender=str(gender),
        current_rating=float(current_rating),
        current_rank=str(current_rank),
        max30_rating=float(max30_rating),
        max30_rank=str(max30_rank),
        max90_rating=float(max90_rating),
        max90_rank=str(max90_rank),
        drs_rating=float(drs_rating),
        drs_rank=str(drs_rank),
        zrcs=float(zrcs),
        source=str(source),
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
