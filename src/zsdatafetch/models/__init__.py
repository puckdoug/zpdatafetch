"""Dataclass models for Zwift Status API responses."""

from zsdatafetch.models.component import ZSComponent
from zsdatafetch.models.incident import ZSIncident, ZSIncidentUpdate
from zsdatafetch.models.maintenance import (
  ZSMaintenance,
  ZSMaintenanceUpdate,
)
from zsdatafetch.models.page import ZSPage
from zsdatafetch.models.status import ZSStatus
from zsdatafetch.models.summary import ZSSummary

__all__ = [
  'ZSComponent',
  'ZSIncident',
  'ZSIncidentUpdate',
  'ZSMaintenance',
  'ZSMaintenanceUpdate',
  'ZSPage',
  'ZSStatus',
  'ZSSummary',
]
