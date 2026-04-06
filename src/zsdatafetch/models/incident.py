"""ZSIncident and ZSIncidentUpdate dataclasses."""

from dataclasses import asdict, dataclass, field
from typing import Any

from zsdatafetch.models.component import ZSComponent


@dataclass(slots=True)
class ZSIncidentUpdate:
  """A single update entry within an incident timeline.

  Attributes:
    id: Update identifier
    status: Update status ("investigating", "identified",
      "monitoring", "resolved")
    body: Update message text
    incident_id: Parent incident identifier
    created_at: ISO 8601 creation timestamp
    updated_at: ISO 8601 last update timestamp
    display_at: ISO 8601 display timestamp
    affected_components: List of affected component dicts
    deliver_notifications: Whether notifications were sent
    custom_tweet: Custom tweet text if any
    tweet_id: Associated tweet ID if any
  """

  id: str = ''
  status: str = ''
  body: str = ''
  incident_id: str = ''
  created_at: str = ''
  updated_at: str = ''
  display_at: str = ''
  affected_components: list[dict[str, str]] = field(
    default_factory=list,
  )
  deliver_notifications: bool = False
  custom_tweet: str | None = None
  tweet_id: str | None = None
  _excluded: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZSIncidentUpdate':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSIncidentUpdate instance with parsed fields
    """
    known_fields = {
      'id', 'status', 'body', 'incident_id',
      'created_at', 'updated_at', 'display_at',
      'affected_components', 'deliver_notifications',
      'custom_tweet', 'tweet_id',
    }

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    return cls(
      id=str(data.get('id', '')),
      status=str(data.get('status', '')),
      body=str(data.get('body', '')),
      incident_id=str(data.get('incident_id', '')),
      created_at=str(data.get('created_at', '')),
      updated_at=str(data.get('updated_at', '')),
      display_at=str(data.get('display_at', '')),
      affected_components=data.get('affected_components', []),
      deliver_notifications=bool(
        data.get('deliver_notifications', False),
      ),
      custom_tweet=data.get('custom_tweet'),
      tweet_id=data.get('tweet_id'),
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


@dataclass(slots=True)
class ZSIncident:
  """A full incident with its update timeline.

  Attributes:
    id: Incident identifier
    name: Incident title
    status: Current status ("investigating", "identified",
      "monitoring", "resolved")
    created_at: ISO 8601 creation timestamp
    updated_at: ISO 8601 last update timestamp
    monitoring_at: ISO 8601 timestamp when monitoring began
    resolved_at: ISO 8601 timestamp when resolved
    impact: Impact level ("none", "minor", "major", "critical")
    shortlink: Short URL for the incident
    started_at: ISO 8601 timestamp when incident started
    page_id: Parent page identifier
    incident_updates: Timeline of updates
    components: Affected components
  """

  id: str = ''
  name: str = ''
  status: str = ''
  created_at: str = ''
  updated_at: str = ''
  monitoring_at: str | None = None
  resolved_at: str | None = None
  impact: str = ''
  shortlink: str = ''
  started_at: str = ''
  page_id: str = ''
  incident_updates: list[ZSIncidentUpdate] = field(
    default_factory=list,
  )
  components: list[ZSComponent] = field(default_factory=list)
  _excluded: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZSIncident':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSIncident instance with parsed fields
    """
    known_fields = {
      'id', 'name', 'status', 'created_at', 'updated_at',
      'monitoring_at', 'resolved_at', 'impact', 'shortlink',
      'started_at', 'page_id', 'incident_updates', 'components',
    }

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    updates = [
      ZSIncidentUpdate.from_dict(u)
      for u in data.get('incident_updates', [])
      if isinstance(u, dict)
    ]
    components = [
      ZSComponent.from_dict(c)
      for c in data.get('components', [])
      if isinstance(c, dict)
    ]

    return cls(
      id=str(data.get('id', '')),
      name=str(data.get('name', '')),
      status=str(data.get('status', '')),
      created_at=str(data.get('created_at', '')),
      updated_at=str(data.get('updated_at', '')),
      monitoring_at=data.get('monitoring_at'),
      resolved_at=data.get('resolved_at'),
      impact=str(data.get('impact', '')),
      shortlink=str(data.get('shortlink', '')),
      started_at=str(data.get('started_at', '')),
      page_id=str(data.get('page_id', '')),
      incident_updates=updates,
      components=components,
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
