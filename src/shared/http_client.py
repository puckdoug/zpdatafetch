"""Shared HTTP client utilities and base classes.

Used by both zpdatafetch and zrdatafetch packages.

This module provides:
1. Retry logic functions for both sync and async HTTP clients
2. Abstract base classes for consistent client lifecycle management

Used by both packages to eliminate duplication in HTTP handling patterns.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import anyio
import httpx

from shared.exceptions import NetworkError

# ==============================================================================
# RETRY LOGIC FUNCTIONS
# ==============================================================================


def fetch_with_retry_sync(
  client: httpx.Client,
  url: str,
  method: str = 'GET',
  max_retries: int = 3,
  backoff_factor: float = 1.0,
  logger: logging.Logger | None = None,
  **kwargs: Any,
) -> httpx.Response:
  """Fetch URL with exponential backoff retry logic (sync variant).

  Retries on transient errors (connection errors, timeouts, 5xx errors)
  but not on client errors (4xx).

  Args:
    client: httpx.Client instance
    url: URL to fetch
    method: HTTP method (default: 'GET')
    max_retries: Maximum number of retry attempts (default: 3)
    backoff_factor: Multiplier for exponential backoff (default: 1.0)
    logger: Optional logger instance for debug/warning output
    **kwargs: Additional arguments to pass to client.request()

  Returns:
    httpx.Response: The successful response

  Raises:
    NetworkError: If all retries are exhausted
  """
  if logger is None:
    logger = logging.getLogger(__name__)

  last_exception: Exception | None = None

  for attempt in range(max_retries):
    try:
      logger.debug(f'Attempt {attempt + 1}/{max_retries}: {method} {url}')
      response = client.request(method, url, **kwargs)
      response.raise_for_status()
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
      time.sleep(wait_time)
    except httpx.HTTPStatusError as e:
      if 500 <= e.response.status_code < 600:
        last_exception = e
        if attempt == max_retries - 1:
          break
        wait_time = backoff_factor * (2**attempt)
        logger.warning(
          f'Server error ({e.response.status_code}) on attempt '
          f'{attempt + 1}: {e}. Retrying in {wait_time:.1f}s...',
        )
        time.sleep(wait_time)
      else:
        # Client errors (4xx) - don't retry, re-raise for caller to handle
        raise
    except httpx.RequestError as e:
      last_exception = e
      if attempt == max_retries - 1:
        break
      wait_time = backoff_factor * (2**attempt)
      logger.warning(
        f'Request error on attempt {attempt + 1}: {e}. '
        f'Retrying in {wait_time:.1f}s...',
      )
      time.sleep(wait_time)

  if last_exception:
    logger.error(f'Max retries ({max_retries}) exhausted: {last_exception}')
    raise NetworkError(
      f'Failed after {max_retries} attempts: {last_exception}',
    ) from last_exception

  raise NetworkError(f'Unexpected error fetching {url}')


async def fetch_with_retry_async(
  client: httpx.AsyncClient,
  url: str,
  method: str = 'GET',
  max_retries: int = 3,
  backoff_factor: float = 1.0,
  logger: logging.Logger | None = None,
  **kwargs: Any,
) -> httpx.Response:
  """Fetch URL with exponential backoff retry logic (async variant).

  Async version using anyio.sleep() for compatibility with both asyncio
  and trio.

  Args:
    client: httpx.AsyncClient instance
    url: URL to fetch
    method: HTTP method (default: 'GET')
    max_retries: Maximum number of retry attempts (default: 3)
    backoff_factor: Multiplier for exponential backoff (default: 1.0)
    logger: Optional logger instance for debug/warning output
    **kwargs: Additional arguments to pass to client.request()

  Returns:
    httpx.Response: The successful response

  Raises:
    NetworkError: If all retries are exhausted
  """
  if logger is None:
    logger = logging.getLogger(__name__)

  last_exception: Exception | None = None

  for attempt in range(max_retries):
    try:
      logger.debug(f'Attempt {attempt + 1}/{max_retries}: {method} {url}')
      response = await client.request(method, url, **kwargs)
      response.raise_for_status()
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
        # Client errors (4xx) - don't retry, re-raise for caller to handle
        raise
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
    raise NetworkError(
      f'Failed after {max_retries} attempts: {last_exception}',
    ) from last_exception

  raise NetworkError(f'Unexpected error fetching {url}')


# ==============================================================================
# ABSTRACT BASE CLASSES
# ==============================================================================


class BaseHTTPClient(ABC):
  """Abstract base class for sync HTTP clients.

  Provides template methods and common lifecycle management for HTTP clients.
  Subclasses implement hooks for package-specific behavior.
  """

  _client: httpx.Client | None = None
  _shared_client: httpx.Client | None = None
  _owns_client: bool = False

  # ----------------------------------------------------------------------------
  # TEMPLATE METHODS - Override in subclasses
  # ----------------------------------------------------------------------------

  @abstractmethod
  def _create_client(self) -> httpx.Client:
    """Create and configure an HTTP client.

    Subclasses implement this to provide package-specific client configuration.

    Returns:
      Configured httpx.Client instance
    """

  def _before_request(
    self,
    url: str,
    method: str = 'GET',
    **kwargs: Any,
  ) -> None:
    """Hook called before making a request.

    Default: no-op. Override in subclasses for pre-request operations like:
    - Authentication checks
    - Rate limit enforcement
    - Custom headers

    Args:
      url: URL being requested
      method: HTTP method
      **kwargs: Additional request parameters
    """

  def _after_request(self, response: httpx.Response) -> None:
    """Hook called after receiving a response.

    Default: no-op. Override in subclasses for post-response operations like:
    - Rate limit tracking
    - Response logging
    - Cache updates

    Args:
      response: The HTTP response
    """

  def _on_close(self) -> None:
    """Hook called when closing the client.

    Default: no-op. Override in subclasses for cleanup operations like:
    - Credential clearing
    - Session cleanup
    - Resource release
    """

  # ----------------------------------------------------------------------------
  # SHARED IMPLEMENTATIONS
  # ----------------------------------------------------------------------------

  def init_client(self, client: httpx.Client | None = None) -> None:
    """Initialize or replace the HTTP client.

    Three-way logic:
    1. If client provided, use it
    2. Else if shared client exists, use it
    3. Else create new client via _create_client()

    Args:
      client: Optional httpx.Client instance to use
    """
    if client:
      self._client = client
    elif self.__class__._shared_client is not None:
      self._client = self.__class__._shared_client
    else:
      self._client = self._create_client()

  @classmethod
  def close_shared_session(cls) -> None:
    """Close the shared HTTP client used for connection pooling.

    Call when done with all batch operations to free resources.
    """
    if cls._shared_client is not None:
      try:
        cls._shared_client.close()
        cls._shared_client = None
      except Exception:
        pass

  def close(self) -> None:
    """Close the HTTP client and clean up resources.

    Calls _on_close() hook for subclass-specific cleanup, then closes
    the client if this instance owns it.
    """
    self._on_close()

    if self._client and self._owns_client:
      try:
        self._client.close()
      except Exception:
        pass

  def __enter__(self) -> 'BaseHTTPClient':
    """Enter context manager."""
    return self

  def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
    """Exit context manager - ensure cleanup."""
    self.close()
    return False


class AsyncBaseHTTPClient(ABC):
  """Abstract base class for async HTTP clients.

  Async version of BaseHTTPClient with same pattern but async methods.
  """

  _client: httpx.AsyncClient | None = None
  _shared_client: httpx.AsyncClient | None = None
  _owns_client: bool = False

  # ----------------------------------------------------------------------------
  # TEMPLATE METHODS - Override in subclasses
  # ----------------------------------------------------------------------------

  @abstractmethod
  async def _create_client(self) -> httpx.AsyncClient:
    """Create and configure an async HTTP client.

    Args:
      Returns: Configured httpx.AsyncClient instance
    """

  async def _before_request(
    self,
    url: str,
    method: str = 'GET',
    **kwargs: Any,
  ) -> None:
    """Hook called before making a request.

    Default: no-op. Override for pre-request operations.
    """

  async def _after_request(self, response: httpx.Response) -> None:
    """Hook called after receiving a response.

    Default: no-op. Override for post-response operations.
    """

  async def _on_close(self) -> None:
    """Hook called when closing the client.

    Default: no-op. Override for cleanup operations.
    """

  # ----------------------------------------------------------------------------
  # SHARED IMPLEMENTATIONS
  # ----------------------------------------------------------------------------

  async def init_client(self, client: httpx.AsyncClient | None = None) -> None:
    """Initialize or replace the async HTTP client.

    Three-way logic:
    1. If client provided, use it
    2. Else if shared client exists, use it
    3. Else create new client via _create_client()

    Args:
      client: Optional httpx.AsyncClient instance to use
    """
    if client:
      self._client = client
    elif self.__class__._shared_client is not None:
      self._client = self.__class__._shared_client
    else:
      self._client = await self._create_client()

  @classmethod
  async def close_shared_session(cls) -> None:
    """Close the shared async HTTP client.

    Call when done with all batch operations.
    """
    if cls._shared_client is not None:
      try:
        await cls._shared_client.aclose()
        cls._shared_client = None
      except Exception:
        pass

  async def aclose(self) -> None:
    """Close the async HTTP client and clean up resources.

    Calls _on_close() hook, then closes the client if owned.
    """
    await self._on_close()

    if self._client and self._owns_client:
      try:
        await self._client.aclose()
      except Exception:
        pass

  async def __aenter__(self) -> 'AsyncBaseHTTPClient':
    """Enter async context manager."""
    return self

  async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
    """Exit async context manager."""
    await self.aclose()
    return False
