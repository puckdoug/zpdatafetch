"""Zwiftracing data fetching library.

A Python library for fetching and managing Zwiftracing data including:
- Rider ratings and rankings
- Race results
- Team/club rosters

This library provides both synchronous and asynchronous APIs for flexible
integration into applications.

Basic Usage:
  from zrdatafetch import ZRRating

  rating = ZRRating(zwift_id=12345)
  rating.fetch()
  print(rating.json())

For command-line usage:
  zrdata rating 12345
  zrdata result 3590800
  zrdata team 456
"""

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.config import Config
from zrdatafetch.exceptions import (
  ZRAuthenticationError,
  ZRConfigError,
  ZRNetworkError,
)
from zrdatafetch.logging_config import setup_logging
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrresult import ZRResult, ZRRiderResult
from zrdatafetch.zrrider import ZRRider
from zrdatafetch.zrteam import ZRTeam, ZRTeamRider

# Backwards compatibility aliases for async classes
# Note: These classes now support both sync (fetch) and async (afetch) methods
AsyncZRRider = ZRRider
AsyncZRResult = ZRResult
AsyncZRTeam = ZRTeam

__all__ = [
  # Base classes
  'ZR_obj',
  'AsyncZR_obj',
  # Configuration
  'Config',
  # Data classes (synchronous)
  'ZRRider',
  'ZRResult',
  'ZRRiderResult',
  'ZRTeam',
  'ZRTeamRider',
  # Data classes (asynchronous) - Aliases for backwards compatibility
  'AsyncZRRider',  # Alias for ZRRider (supports both sync and async)
  'AsyncZRResult',  # Alias for ZRResult (supports both sync and async)
  'AsyncZRTeam',  # Alias for ZRTeam (supports both sync and async)
  # Exceptions
  'ZRAuthenticationError',
  'ZRNetworkError',
  'ZRConfigError',
  # Logging
  'setup_logging',
]
