"""ZSPage dataclass for Statuspage page metadata."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ZSPage:
  """Page metadata shared across all Zwift Status API responses.

  Attributes:
    id: Statuspage page identifier
    name: Page display name (e.g., "Zwift")
    url: Page URL
    time_zone: IANA time zone string
    updated_at: ISO 8601 timestamp of last update
  """

  id: str = ''
  name: str = ''
  url: str = ''
  time_zone: str = ''
  updated_at: str = ''
  _excluded: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZSPage':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSPage instance with parsed fields
    """
    known_fields = {
      'id', 'name', 'url', 'time_zone', 'updated_at',
    }

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    return cls(
      id=str(data.get('id', '')),
      name=str(data.get('name', '')),
      url=str(data.get('url', '')),
      time_zone=str(data.get('time_zone', '')),
      updated_at=str(data.get('updated_at', '')),
      _extra=extra,
    )

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private fields."""
    result = asdict(self)
    result.pop('_extra', None)
    result.pop('_excluded', None)
    return result

  def excluded(self) -> dict[str, Any]:
    """Return recognized but unhandled fields."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return unknown fields from API response."""
    return dict(self._extra)
