"""Async base class for Zwift Status data objects.

Provides async HTTP client for fetching from the Zwift Status API.
This API is public and unauthenticated.
"""

from typing import Any, ClassVar

import httpx2

from shared.error_helpers import format_network_error
from shared.exceptions import NetworkError
from shared.http_client import fetch_with_retry_async
from zsdatafetch.logging_config import get_logger

logger = get_logger(__name__)


class AsyncZS_obj:
  """Async base class for Zwift Status data objects.

  Provides:
    - Async HTTP client
    - Retry logic via shared.http_client
    - Context manager support

  No authentication required.

  Attributes:
    _client: Async HTTP client instance
    _base_url: Base URL for all API requests
  """

  _base_url: ClassVar[str] = 'https://status.zwift.com/api/v2'

  def __init__(self) -> None:
    """Initialize AsyncZS_obj."""
    self._client: httpx2.AsyncClient | None = None

  async def init_client(self) -> None:
    """Initialize the async HTTP client."""
    if self._client is None:
      logger.debug(
        'Creating async HTTP client for Zwift Status',
      )
      self._client = httpx2.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
      )

  async def close(self) -> None:
    """Close the async HTTP client."""
    if self._client is not None:
      logger.debug('Closing async HTTP client')
      await self._client.aclose()
      self._client = None

  async def __aenter__(self) -> 'AsyncZS_obj':
    """Enter async context manager."""
    await self.init_client()
    return self

  async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: Any,
  ) -> bool:
    """Exit async context manager."""
    await self.close()
    return False

  async def fetch_json(self, endpoint: str) -> str:
    """Fetch JSON from an API endpoint asynchronously.

    Args:
      endpoint: API endpoint path (e.g., '/summary.json')

    Returns:
      Raw JSON response as a string

    Raises:
      NetworkError: If the request fails
    """
    if self._client is None:
      await self.init_client()
    assert self._client is not None

    url = f'{self._base_url}{endpoint}'

    try:
      response = await fetch_with_retry_async(
        self._client,
        url,
        logger=logger,
      )
      return response.text
    except httpx2.HTTPStatusError as e:
      logger.error(
        f'HTTP error GET {endpoint}: {e.response.status_code}',
      )
      raise NetworkError(
        format_network_error(
          'get request',
          endpoint,
          e,
          status_code=e.response.status_code,
        ),
      ) from e
    except httpx2.RequestError as e:
      logger.error(f'Network error GET {endpoint}: {e}')
      raise NetworkError(
        format_network_error('get request', endpoint, e),
      ) from e
