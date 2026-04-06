"""ZSComponent dataclass for service components."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ZSComponent:
  """A service component from the Zwift Status API.

  Represents a monitored service (e.g., "Game", "Web", "Companion App").
  Group components contain child component IDs in the components field.

  Attributes:
    id: Component identifier
    name: Display name
    status: Current status ("operational", "degraded_performance",
      "partial_outage", "major_outage")
    description: Optional description text
    position: Display order position
    created_at: ISO 8601 creation timestamp
    updated_at: ISO 8601 last update timestamp
    group_id: Parent group component ID (None if top-level)
    group: Whether this is a group container
    only_show_if_degraded: Hide when operational
    components: Child component IDs (for group components)
    showcase: Whether to showcase this component
    start_date: Optional start date
    page_id: Parent page identifier
  """

  id: str = ''
  name: str = ''
  status: str = ''
  description: str | None = None
  position: int = 0
  created_at: str = ''
  updated_at: str = ''
  group_id: str | None = None
  group: bool = False
  only_show_if_degraded: bool = False
  components: list[str] = field(default_factory=list)
  showcase: bool = False
  start_date: str | None = None
  page_id: str = ''
  _excluded: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZSComponent':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSComponent instance with parsed fields
    """
    known_fields = {
      'id', 'name', 'status', 'description', 'position',
      'created_at', 'updated_at', 'group_id', 'group',
      'only_show_if_degraded', 'components', 'showcase',
      'start_date', 'page_id',
    }

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    raw_components = data.get('components', [])
    component_ids: list[str] = []
    if isinstance(raw_components, list):
      component_ids = [str(c) for c in raw_components]

    return cls(
      id=str(data.get('id', '')),
      name=str(data.get('name', '')),
      status=str(data.get('status', '')),
      description=data.get('description'),
      position=int(data.get('position', 0)),
      created_at=str(data.get('created_at', '')),
      updated_at=str(data.get('updated_at', '')),
      group_id=data.get('group_id'),
      group=bool(data.get('group', False)),
      only_show_if_degraded=bool(
        data.get('only_show_if_degraded', False),
      ),
      components=component_ids,
      showcase=bool(data.get('showcase', False)),
      start_date=data.get('start_date'),
      page_id=str(data.get('page_id', '')),
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
