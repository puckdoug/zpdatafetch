"""ZwiftRanking data fetching library.

A Python library for fetching and managing ZwiftRanking data including:
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

from zrdatafetch.config import Config
from zrdatafetch.exceptions import (
  ZRAuthenticationError,
  ZRConfigError,
  ZRNetworkError,
)
from zrdatafetch.logging_config import setup_logging
from zrdatafetch.zr import ZR_obj
from zrdatafetch.zrrider import ZRRider

__all__ = [
  # Base classes
  'ZR_obj',
  # Configuration
  'Config',
  # Data classes
  'ZRRider',
  # Exceptions
  'ZRAuthenticationError',
  'ZRNetworkError',
  'ZRConfigError',
  # Logging
  'setup_logging',
  # Note: Data classes (ZRResult, ZRTeam) will be added
  # when they are refactored to use dataclasses and inherit from ZR_obj
]
