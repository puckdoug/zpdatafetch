"""ZSStatus dataclass for overall status indicator."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ZSStatus:
  """Overall status indicator from the Zwift Status API.

  Attributes:
    indicator: Status level ("none", "minor", "major", "critical")
    description: Human-readable status (e.g., "All Systems Operational")
  """

  indicator: str = ''
  description: str = ''
  _excluded: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZSStatus':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSStatus instance with parsed fields
    """
    known_fields = {'indicator', 'description'}

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    return cls(
      indicator=str(data.get('indicator', '')),
      description=str(data.get('description', '')),
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
