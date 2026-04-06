"""ZSMaintenance and ZSMaintenanceUpdate dataclasses."""

from dataclasses import asdict, dataclass, field
from typing import Any

from zsdatafetch.models.component import ZSComponent


@dataclass(slots=True)
class ZSMaintenanceUpdate:
  """A single update entry within a maintenance timeline.

  Attributes:
    id: Update identifier
    status: Update status ("scheduled", "in_progress",
      "verifying", "completed")
    body: Update message text
    created_at: ISO 8601 creation timestamp
    updated_at: ISO 8601 last update timestamp
    display_at: ISO 8601 display timestamp
    affected_components: List of affected component dicts
    deliver_notifications: Whether notifications were sent
    custom_tweet: Custom tweet text if any
    tweet_id: Associated tweet ID if any
    scheduled_maintenance_id: Parent maintenance identifier
  """

  id: str = ''
  status: str = ''
  body: str = ''
  created_at: str = ''
  updated_at: str = ''
  display_at: str = ''
  affected_components: list[dict[str, str]] = field(
    default_factory=list,
  )
  deliver_notifications: bool = False
  custom_tweet: str | None = None
  tweet_id: str | None = None
  scheduled_maintenance_id: str = ''
  _excluded: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )

  @classmethod
  def from_dict(
    cls, data: dict[str, Any],
  ) -> 'ZSMaintenanceUpdate':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSMaintenanceUpdate instance with parsed fields
    """
    known_fields = {
      'id', 'status', 'body',
      'created_at', 'updated_at', 'display_at',
      'affected_components', 'deliver_notifications',
      'custom_tweet', 'tweet_id', 'scheduled_maintenance_id',
    }

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    return cls(
      id=str(data.get('id', '')),
      status=str(data.get('status', '')),
      body=str(data.get('body', '')),
      created_at=str(data.get('created_at', '')),
      updated_at=str(data.get('updated_at', '')),
      display_at=str(data.get('display_at', '')),
      affected_components=data.get('affected_components', []),
      deliver_notifications=bool(
        data.get('deliver_notifications', False),
      ),
      custom_tweet=data.get('custom_tweet'),
      tweet_id=data.get('tweet_id'),
      scheduled_maintenance_id=str(
        data.get('scheduled_maintenance_id', ''),
      ),
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
class ZSMaintenance:
  """A scheduled maintenance window with its update timeline.

  Attributes:
    id: Maintenance identifier
    name: Maintenance title
    status: Current status ("scheduled", "in_progress",
      "verifying", "completed")
    created_at: ISO 8601 creation timestamp
    updated_at: ISO 8601 last update timestamp
    monitoring_at: ISO 8601 timestamp when monitoring began
    resolved_at: ISO 8601 timestamp when completed
    impact: Impact type ("maintenance")
    shortlink: Short URL for the maintenance
    started_at: ISO 8601 timestamp when maintenance started
    page_id: Parent page identifier
    scheduled_for: ISO 8601 scheduled start time
    scheduled_until: ISO 8601 scheduled end time
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
  scheduled_for: str = ''
  scheduled_until: str = ''
  incident_updates: list[ZSMaintenanceUpdate] = field(
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
  def from_dict(cls, data: dict[str, Any]) -> 'ZSMaintenance':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSMaintenance instance with parsed fields
    """
    known_fields = {
      'id', 'name', 'status', 'created_at', 'updated_at',
      'monitoring_at', 'resolved_at', 'impact', 'shortlink',
      'started_at', 'page_id', 'scheduled_for',
      'scheduled_until', 'incident_updates', 'components',
    }

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    updates = [
      ZSMaintenanceUpdate.from_dict(u)
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
      scheduled_for=str(data.get('scheduled_for', '')),
      scheduled_until=str(data.get('scheduled_until', '')),
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
