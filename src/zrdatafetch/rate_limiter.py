"""Rate limiting for ZwiftRanking API.

Implements sliding window rate limiting for different API endpoints with
support for standard and premium tier rate limits.
"""

import time
from collections import deque
from typing import Literal

import anyio

from zrdatafetch.logging_config import get_logger

logger = get_logger(__name__)


# ===============================================================================
class RateLimiter:
  """Track and enforce ZwiftRanking API rate limits.

  Implements sliding window rate limiting for different endpoints:
  - Standard tier: Lower request limits per time window
  - Premium tier: Higher request limits per time window

  Supports automatic throttling to respect rate limits.

  Attributes:
    tier: 'standard' or 'premium' tier level
    STANDARD_LIMITS: Dict of endpoint -> (max_requests, window_seconds)
    PREMIUM_LIMITS: Dict of endpoint -> (max_requests, window_seconds)
  """

  # Standard tier limits: (max_requests, window_seconds)
  STANDARD_LIMITS = {
    'clubs': (1, 3600),  # 1 request per 60 minutes
    'results': (1, 60),  # 1 request per 1 minute
    'riders_get': (5, 60),  # 5 requests per 1 minute
    'riders_post': (1, 900),  # 1 request per 15 minutes
  }

  # Premium tier limits: (max_requests, window_seconds)
  PREMIUM_LIMITS = {
    'clubs': (10, 3600),  # 10 requests per 60 minutes
    'results': (1, 60),  # 1 request per 1 minute (same)
    'riders_get': (10, 60),  # 10 requests per 1 minute
    'riders_post': (10, 900),  # 10 requests per 15 minutes
  }

  # -------------------------------------------------------------------------------
  def __init__(self, tier: Literal['standard', 'premium'] = 'standard') -> None:
    """Initialize rate limiter with specified tier.

    Args:
      tier: 'standard' (default) or 'premium' rate limits
    """
    self.tier = tier
    self.limits = self.PREMIUM_LIMITS if tier == 'premium' else self.STANDARD_LIMITS
    self.history: dict[str, deque] = {
      endpoint: deque() for endpoint in self.limits.keys()
    }
    logger.debug(f'Initialized RateLimiter with {tier} tier')

  # -------------------------------------------------------------------------------
  def can_request(self, endpoint: str) -> bool:
    """Check if request is allowed within rate limit.

    Args:
      endpoint: Endpoint key ('clubs', 'results', 'riders_get', 'riders_post')

    Returns:
      True if request is allowed, False if rate limit reached
    """
    if endpoint not in self.limits:
      logger.debug(f'No rate limit configured for endpoint: {endpoint}')
      return True

    max_requests, window = self.limits[endpoint]
    now = time.time()

    # Remove old requests outside window
    history = self.history[endpoint]
    while history and now - history[0] > window:
      history.popleft()

    can_request = len(history) < max_requests
    logger.debug(
      f'Endpoint {endpoint}: {len(history)}/{max_requests} requests in window',
    )
    return can_request

  # -------------------------------------------------------------------------------
  def wait_time(self, endpoint: str) -> float:
    """Calculate seconds to wait before next request is allowed.

    Args:
      endpoint: Endpoint key ('clubs', 'results', 'riders_get', 'riders_post')

    Returns:
      Number of seconds to wait (0.0 if request is allowed now)
    """
    if self.can_request(endpoint):
      return 0.0

    if endpoint not in self.limits:
      return 0.0

    max_requests, window = self.limits[endpoint]
    history = self.history[endpoint]

    if not history:
      return 0.0

    # Time until oldest request expires
    oldest = history[0]
    wait = window - (time.time() - oldest)
    return max(0.0, wait)

  # -------------------------------------------------------------------------------
  def record_request(self, endpoint: str) -> None:
    """Record that a request was made to an endpoint.

    Args:
      endpoint: Endpoint key ('clubs', 'results', 'riders_get', 'riders_post')
    """
    if endpoint in self.history:
      self.history[endpoint].append(time.time())
      logger.debug(f'Recorded request for {endpoint}')

  # -------------------------------------------------------------------------------
  async def wait_if_needed(self, endpoint: str) -> None:
    """Wait if necessary to respect rate limit.

    Checks if a request would exceed the rate limit and waits if needed.
    This should be called before making a request.

    Args:
      endpoint: Endpoint key ('clubs', 'results', 'riders_get', 'riders_post')
    """
    wait = self.wait_time(endpoint)
    if wait > 0:
      logger.warning(
        f'Rate limit reached for {endpoint}, waiting {wait:.1f}s '
        f'({self.tier} tier)',
      )
      await anyio.sleep(wait)
      logger.debug(f'Resuming requests for {endpoint}')

  # -------------------------------------------------------------------------------
  def get_status(self) -> dict:
    """Get current rate limit status for all endpoints.

    Returns:
      Dict with endpoint status including requests used and remaining
    """
    status = {'tier': self.tier, 'endpoints': {}}
    now = time.time()

    for endpoint, (max_requests, window) in self.limits.items():
      history = self.history[endpoint]

      # Remove old requests
      while history and now - history[0] > window:
        history.popleft()

      used = len(history)
      remaining = max(0, max_requests - used)
      oldest = history[0] if history else None
      reset_in = (oldest + window - now) if oldest else 0.0

      status['endpoints'][endpoint] = {
        'used': used,
        'limit': max_requests,
        'remaining': remaining,
        'window_seconds': window,
        'reset_in_seconds': max(0.0, reset_in),
      }

    return status

  # -------------------------------------------------------------------------------
  def set_tier(self, tier: Literal['standard', 'premium']) -> None:
    """Change the tier level.

    Args:
      tier: 'standard' or 'premium'
    """
    self.tier = tier
    self.limits = self.PREMIUM_LIMITS if tier == 'premium' else self.STANDARD_LIMITS
    logger.info(f'Changed rate limit tier to: {tier}')

  # -------------------------------------------------------------------------------
  @staticmethod
  def get_endpoint_type(method: str, endpoint: str) -> str:
    """Determine the endpoint type for rate limiting purposes.

    Args:
      method: HTTP method ('GET' or 'POST')
      endpoint: API endpoint path

    Returns:
      Endpoint key for rate limiting ('clubs', 'results', 'riders_get', etc.)
    """
    if '/clubs/' in endpoint or '/clubs' in endpoint:
      return 'clubs'
    if '/results/' in endpoint or '/results' in endpoint:
      return 'results'
    if '/riders' in endpoint:
      return 'riders_post' if method.upper() == 'POST' else 'riders_get'
    return 'unknown'
