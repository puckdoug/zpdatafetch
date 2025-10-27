"""Async version of the ZR class for asynchronous Zwiftracing API access.

This module provides async/await compatible interfaces for the Zwiftracing API,
allowing for concurrent requests and better performance in async applications.
"""

import json
from typing import Any

import anyio
import httpx

from zrdatafetch.exceptions import ZRNetworkError
from zrdatafetch.logging_config import get_logger
from zrdatafetch.rate_limiter import RateLimiter

logger = get_logger(__name__)


# ===============================================================================
class AsyncZR_obj:
  """Async version of the ZR_obj base class for Zwiftracing API.

  This class provides async/await compatible methods for HTTP requests to
  the Zwiftracing API. It can be used with asyncio for concurrent operations.

  Usage:
    async with AsyncZR_obj() as zr:
      data = await zr.fetch_json('/public/riders/123')

  Or:
    zr = AsyncZR_obj()
    data = await zr.fetch_json('/public/riders/123')
    await zr.close()

  Attributes:
    _base_url: Base URL for Zwiftracing API
    _client: httpx.AsyncClient instance
  """

  _base_url: str = 'https://zwift-ranking.herokuapp.com'
  _shared_client: httpx.AsyncClient | None = None
  _owns_client: bool = False

  # -------------------------------------------------------------------------------
  def __init__(
    self,
    shared_client: bool = False,
    premium: bool = False,
  ) -> None:
    """Initialize the AsyncZR_obj client.

    Args:
      shared_client: Use a shared HTTP client for connection pooling (default: False).
        Useful when creating multiple AsyncZR_obj instances for batch operations.
      premium: Use premium tier rate limits (default: False for standard tier).
    """
    self._client: httpx.AsyncClient | None = None
    self._owns_client = not shared_client
    self.rate_limiter = RateLimiter(tier='premium' if premium else 'standard')

    if shared_client and AsyncZR_obj._shared_client is None:
      logger.debug('Creating shared async HTTP client for connection pooling')
      AsyncZR_obj._shared_client = httpx.AsyncClient(
        base_url=self._base_url,
        timeout=30.0,
        follow_redirects=True,
      )

  # -------------------------------------------------------------------------------
  async def init_client(
    self,
    client: httpx.AsyncClient | None = None,
  ) -> None:
    """Initialize or replace the async HTTP client.

    Args:
      client: Optional httpx.AsyncClient instance to use. If None, uses shared
        client if available, otherwise creates a new client.
    """
    logger.debug('Initializing httpx async client for Zwiftracing')

    if client:
      logger.debug('Using provided httpx async client')
      self._client = client
    elif AsyncZR_obj._shared_client is not None:
      logger.debug('Using shared async HTTP client for connection pooling')
      self._client = AsyncZR_obj._shared_client
    else:
      logger.debug(
        'Creating new httpx async client with HTTPS certificate verification',
      )
      # SECURITY: Explicitly enable certificate verification for HTTPS
      self._client = httpx.AsyncClient(
        base_url=self._base_url,
        timeout=30.0,
        follow_redirects=True,
        verify=True,
      )

  # -------------------------------------------------------------------------------
  async def _fetch_with_retry(
    self,
    endpoint: str,
    method: str = 'GET',
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    **kwargs: Any,
  ) -> httpx.Response:
    """Fetch endpoint with exponential backoff retry logic (async).

    Retries on transient errors (connection errors, timeouts) but not on
    client errors (4xx) or authentication errors. Respects rate limits
    by waiting before requests and handling 429 responses.

    Args:
      endpoint: API endpoint path
      method: HTTP method (default: 'GET')
      max_retries: Maximum number of retry attempts (default: 3)
      backoff_factor: Multiplier for exponential backoff (default: 1.0)
      **kwargs: Additional arguments to pass to httpx client method

    Returns:
      httpx.Response: The successful response

    Raises:
      ZRNetworkError: If all retries are exhausted or rate limit exceeded
    """
    if self._client is None:
      await self.init_client()

    # Check rate limits before attempting request
    endpoint_type = RateLimiter.get_endpoint_type(method, endpoint)
    await self.rate_limiter.wait_if_needed(endpoint_type)

    last_exception: Exception | None = None

    for attempt in range(max_retries):
      try:
        logger.debug(f'Attempt {attempt + 1}/{max_retries}: {method} {endpoint}')
        response = await self._client.request(method, endpoint, **kwargs)
        response.raise_for_status()

        # Record successful request for rate limiting
        self.rate_limiter.record_request(endpoint_type)
        return response

      except (httpx.ConnectError, httpx.TimeoutException) as e:
        last_exception = e
        if attempt == max_retries - 1:
          break
        wait_time = backoff_factor * (2**attempt)
        logger.warning(
          f'Transient network error on attempt {attempt + 1}: {e}. '
          f'Retrying in {wait_time:.1f}s...',
        )
        await anyio.sleep(wait_time)

      except httpx.HTTPStatusError as e:
        # Handle rate limit error (429)
        if e.response.status_code == 429:
          tier = self.rate_limiter.tier
          raise ZRNetworkError(
            f'Rate limit exceeded ({tier} tier). '
            f'Status: {e.response.status_code}. '
            f'Current rate limit status: {self.rate_limiter.get_status()}',
          ) from e

        if 500 <= e.response.status_code < 600:
          last_exception = e
          if attempt == max_retries - 1:
            break
          wait_time = backoff_factor * (2**attempt)
          logger.warning(
            f'Server error ({e.response.status_code}) on attempt '
            f'{attempt + 1}: {e}. Retrying in {wait_time:.1f}s...',
          )
          await anyio.sleep(wait_time)
        else:
          raise ZRNetworkError(f'HTTP error: {e}') from e

      except httpx.RequestError as e:
        last_exception = e
        if attempt == max_retries - 1:
          break
        wait_time = backoff_factor * (2**attempt)
        logger.warning(
          f'Request error on attempt {attempt + 1}: {e}. '
          f'Retrying in {wait_time:.1f}s...',
        )
        await anyio.sleep(wait_time)

    if last_exception:
      logger.error(f'Max retries ({max_retries}) exhausted: {last_exception}')
      raise ZRNetworkError(
        f'Failed after {max_retries} attempts: {last_exception}',
      ) from last_exception

    raise ZRNetworkError(f'Unexpected error fetching {endpoint}')

  # -------------------------------------------------------------------------------
  async def fetch_json(
    self,
    endpoint: str,
    method: str = 'GET',
    max_retries: int = 3,
    **kwargs: Any,
  ) -> dict | list:
    """Fetch JSON data from a Zwiftracing endpoint (async).

    Automatically initializes client if needed. Retries on transient
    network errors. Returns an empty dict if the response cannot be decoded
    as JSON.

    Args:
      endpoint: API endpoint path (e.g., '/public/riders/123')
      method: HTTP method ('GET' or 'POST'). Default: 'GET'
      max_retries: Maximum number of retry attempts for transient errors
      **kwargs: Additional arguments passed to httpx request method
        (e.g., headers, params, json, etc.)

    Returns:
      Dictionary or list containing the parsed JSON response, or empty dict
      if JSON decoding fails

    Raises:
      ZRNetworkError: If the HTTP request fails after retries

    Example:
      # GET request
      data = await zr.fetch_json('/public/riders/12345')
      # Returns dict with rider data

      # POST request (batch)
      data = await zr.fetch_json(
        '/public/riders',
        method='POST',
        headers={'Authorization': 'token'},
        json=[12345, 67890]
      )
      # Returns list of rider dicts
    """
    try:
      logger.debug(f'Fetching JSON from: {endpoint}')
      pres = await self._fetch_with_retry(
        endpoint,
        method=method,
        max_retries=max_retries,
        **kwargs,
      )

      try:
        res = pres.json()
        logger.debug(f'Successfully fetched and parsed JSON from {endpoint}')
      except json.decoder.JSONDecodeError:
        logger.warning(
          f'Could not decode JSON from {endpoint}, returning empty dict',
        )
        res = {}
      return res
    except ZRNetworkError:
      raise
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error fetching {endpoint}: {e}')
      raise ZRNetworkError(f'HTTP error fetching {endpoint}: {e}') from e
    except httpx.RequestError as e:
      logger.error(f'Network error fetching {endpoint}: {e}')
      raise ZRNetworkError(f'Network error fetching {endpoint}: {e}') from e

  # -------------------------------------------------------------------------------
  @classmethod
  async def close_shared_session(cls) -> None:
    """Close the shared async client if it exists.

    This should be called when your application is shutting down to ensure
    the shared connection pool is properly closed. Only needed if you used
    shared_client=True when creating instances.

    Example:
      await AsyncZR_obj.close_shared_session()
    """
    if cls._shared_client:
      logger.debug('Closing shared async HTTP client')
      await cls._shared_client.aclose()
      cls._shared_client = None
      logger.debug('Shared async client closed')

  # -------------------------------------------------------------------------------
  async def close(self) -> None:
    """Close the HTTP client and clean up resources.

    This method should be called when you're done with the AsyncZR_obj instance
    to ensure proper cleanup of network resources.
    """
    if self._client and self._owns_client:
      try:
        await self._client.aclose()
        logger.debug('Async HTTP client closed successfully')
      except Exception as e:
        logger.error(f'Could not close async client properly: {e}')

  # -------------------------------------------------------------------------------
  async def __aenter__(self) -> 'AsyncZR_obj':
    """Enter async context manager - return self for use in 'async with' statement."""
    return self

  # -------------------------------------------------------------------------------
  async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
    """Exit async context manager - ensure cleanup always happens.

    Args:
      exc_type: Exception type if an exception occurred
      exc_val: Exception value if an exception occurred
      exc_tb: Exception traceback if an exception occurred

    Returns:
      False to propagate any exceptions that occurred
    """
    await self.close()
    return False

  # -------------------------------------------------------------------------------
  def __del__(self) -> None:
    """Fallback cleanup if context manager not used.

    Note: This uses a synchronous close which may not work properly
    for async clients. Always prefer using async with or explicitly
    calling await close().
    """
    # We can't call async close() from __del__, so just log a warning
    if self._client and self._owns_client:
      logger.warning(
        'AsyncZR_obj instance deleted without proper cleanup. '
        'Use "async with AsyncZR_obj()" or call "await zr.close()" explicitly.',
      )
