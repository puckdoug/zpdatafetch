"""Base class for Zwift Status data objects (synchronous).

Provides shared HTTP client for fetching from the Zwift Status API.
This API is public and unauthenticated.
"""

from typing import ClassVar

import httpx

from shared.error_helpers import format_network_error
from shared.exceptions import NetworkError
from shared.http_client import fetch_with_retry_sync
from zsdatafetch.logging_config import get_logger

logger = get_logger(__name__)


class ZS_obj:
  """Base class for all Zwift Status data objects.

  Provides:
    - Shared HTTP client with connection pooling
    - Retry logic via shared.http_client
    - Error handling with NetworkError

  No authentication required — the Zwift Status API is public.

  Attributes:
    _client: Shared HTTP client
    _base_url: Base URL for all API requests
  """

  _client: ClassVar[httpx.Client | None] = None
  _base_url: ClassVar[str] = 'https://status.zwift.com/api/v2'

  @classmethod
  def get_client(cls) -> httpx.Client:
    """Get or create a shared HTTP client.

    Returns:
      httpx.Client configured for Zwift Status API
    """
    if cls._client is None:
      logger.debug('Creating shared HTTP client for Zwift Status')
      cls._client = httpx.Client(
        timeout=30.0,
        follow_redirects=True,
      )
    return cls._client

  @classmethod
  def close_client(cls) -> None:
    """Close the shared HTTP client."""
    if cls._client is not None:
      logger.debug('Closing shared HTTP client')
      cls._client.close()
      cls._client = None

  def fetch_json(self, endpoint: str) -> str:
    """Fetch JSON from an API endpoint.

    Args:
      endpoint: API endpoint path (e.g., '/summary.json')

    Returns:
      Raw JSON response as a string

    Raises:
      NetworkError: If the request fails
    """
    client = self.get_client()
    url = f'{self._base_url}{endpoint}'

    try:
      response = fetch_with_retry_sync(
        client, url, logger=logger,
      )
      return response.text
    except httpx.HTTPStatusError as e:
      logger.error(
        f'HTTP error GET {endpoint}: {e.response.status_code}',
      )
      raise NetworkError(
        format_network_error(
          'get request', endpoint, e,
          status_code=e.response.status_code,
        ),
      ) from e
    except httpx.RequestError as e:
      logger.error(f'Network error GET {endpoint}: {e}')
      raise NetworkError(
        format_network_error('get request', endpoint, e),
      ) from e
