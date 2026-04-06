"""ZSSummary container dataclass for summary endpoint response."""

from dataclasses import asdict, dataclass, field
from typing import Any

from zsdatafetch.models.component import ZSComponent
from zsdatafetch.models.incident import ZSIncident
from zsdatafetch.models.maintenance import ZSMaintenance
from zsdatafetch.models.page import ZSPage
from zsdatafetch.models.status import ZSStatus


@dataclass(slots=True)
class ZSSummary:
  """Container for the full summary endpoint response.

  Attributes:
    page: Page metadata
    status: Overall status indicator
    components: List of service components
    incidents: List of recent incidents
    scheduled_maintenances: List of scheduled maintenance windows
  """

  page: ZSPage = field(default_factory=ZSPage)
  status: ZSStatus = field(default_factory=ZSStatus)
  components: list[ZSComponent] = field(default_factory=list)
  incidents: list[ZSIncident] = field(default_factory=list)
  scheduled_maintenances: list[ZSMaintenance] = field(
    default_factory=list,
  )
  _excluded: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )
  _extra: dict[str, Any] = field(
    default_factory=dict, repr=False,
  )

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZSSummary':
    """Create instance from API response dict.

    Args:
      data: Dictionary from API response

    Returns:
      ZSSummary instance with parsed fields
    """
    known_fields = {
      'page', 'status', 'components',
      'incidents', 'scheduled_maintenances',
    }

    extra: dict[str, Any] = {}
    for key, value in data.items():
      if key not in known_fields:
        extra[key] = value

    page_data = data.get('page', {})
    page = (
      ZSPage.from_dict(page_data)
      if isinstance(page_data, dict) else ZSPage()
    )

    status_data = data.get('status', {})
    status = (
      ZSStatus.from_dict(status_data)
      if isinstance(status_data, dict) else ZSStatus()
    )

    components = [
      ZSComponent.from_dict(c)
      for c in (data.get('components') or [])
      if isinstance(c, dict)
    ]
    incidents = [
      ZSIncident.from_dict(i)
      for i in (data.get('incidents') or [])
      if isinstance(i, dict)
    ]
    maintenances = [
      ZSMaintenance.from_dict(m)
      for m in (data.get('scheduled_maintenances') or [])
      if isinstance(m, dict)
    ]

    return cls(
      page=page,
      status=status,
      components=components,
      incidents=incidents,
      scheduled_maintenances=maintenances,
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
