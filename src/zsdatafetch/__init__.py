"""Zwift Status data fetching library.

A Python library for fetching Zwift service status data including:
- Overall service status and components
- Incidents and unresolved incidents
- Scheduled maintenance windows

This library provides both synchronous and asynchronous APIs.

Basic Usage:
  from zsdatafetch import ZSSummaryFetch

  summary = ZSSummaryFetch().fetch()
  print(summary.status.description)
  for comp in summary.components:
    print(f"  {comp.name}: {comp.status}")

For command-line usage:
  zsdata status
  zsdata incidents
  zsdata maintenance --upcoming
"""

from zsdatafetch.async_zs import AsyncZS_obj
from zsdatafetch.logging_config import setup_logging
from zsdatafetch.models import (
  ZSComponent,
  ZSIncident,
  ZSIncidentUpdate,
  ZSMaintenance,
  ZSMaintenanceUpdate,
  ZSPage,
  ZSStatus,
  ZSSummary,
)
from zsdatafetch.zs import ZS_obj
from zsdatafetch.zsincidentfetch import ZSIncidentFetch
from zsdatafetch.zsmaintenancefetch import ZSMaintenanceFetch
from zsdatafetch.zssummaryfetch import ZSSummaryFetch

__all__ = [
  # Base classes
  'ZS_obj',
  'AsyncZS_obj',
  # Fetcher classes
  'ZSSummaryFetch',
  'ZSIncidentFetch',
  'ZSMaintenanceFetch',
  # Model classes
  'ZSComponent',
  'ZSIncident',
  'ZSIncidentUpdate',
  'ZSMaintenance',
  'ZSMaintenanceUpdate',
  'ZSPage',
  'ZSStatus',
  'ZSSummary',
  # Exceptions (lazy-loaded)
  'NetworkError',
  # Logging
  'setup_logging',
]


def __getattr__(name: str) -> type[Exception]:
  """Lazy import of exceptions to avoid circular imports."""
  if name == 'NetworkError':
    from shared.exceptions import NetworkError

    return NetworkError
  raise AttributeError(
    f'module {__name__!r} has no attribute {name!r}',
  )
