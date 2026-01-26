"""Zwiftracing data fetching library.

A Python library for fetching and managing Zwiftracing data including:
- Rider ratings and rankings
- Race results
- Team/club rosters

This library provides both synchronous and asynchronous APIs for flexible
integration into applications.

Basic Usage (Separate Fetcher and Dataclass Pattern):
  from zrdatafetch import ZRRiderFetch

  fetcher = ZRRiderFetch()
  riders = fetcher.fetch(12345, 67890)  # Returns dict[int, ZRRider]
  for zwift_id, rider in riders.items():
    print(f"{rider.name}: {rider.current_rating}")

For command-line usage:
  zrdata rider 12345
  zrdata result 3590800
  zrdata team 456
"""

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.logging_config import setup_logging
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrraceresult import ZRRaceResult, ZRRiderResult
from zrdatafetch.zrresultfetch import ZRResultFetch

# Pure dataclasses (data containers, no fetch logic)
from zrdatafetch.zrrider import ZRRider

# Fetcher classes (handle API requests, return native dataclass objects)
from zrdatafetch.zrriderfetch import ZRRiderFetch
from zrdatafetch.zrteamfetch import ZRTeamFetch
from zrdatafetch.zrteamroster import ZRTeamMember, ZRTeamRoster

__all__ = [
  # Base classes
  'ZR_obj',
  'AsyncZR_obj',
  # Configuration
  'Config',
  # Fetcher classes (return native dataclass objects)
  'ZRRiderFetch',
  'ZRResultFetch',
  'ZRTeamFetch',
  # Pure dataclasses (no fetch logic)
  'ZRRider',
  'ZRRaceResult',
  'ZRRiderResult',
  'ZRTeamMember',
  'ZRTeamRoster',
  # Exceptions
  'AuthenticationError',
  'NetworkError',
  'ConfigError',
  # Logging
  'setup_logging',
]


def __getattr__(name: str) -> type[Exception]:
  """Lazy import of exceptions to avoid circular imports."""
  if name == 'AuthenticationError':
    from shared.exceptions import AuthenticationError

    return AuthenticationError
  if name == 'NetworkError':
    from shared.exceptions import NetworkError

    return NetworkError
  if name == 'ConfigError':
    from shared.exceptions import ConfigError

    return ConfigError
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
