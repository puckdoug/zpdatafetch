"""Base class for Zwiftracing data objects.

Provides common functionality for HTTP requests, error handling, and JSON
serialization for all Zwiftracing data classes.
"""

import json
from typing import Any, ClassVar

import httpx

from zrdatafetch.exceptions import ZRNetworkError
from zrdatafetch.logging_config import get_logger

logger = get_logger(__name__)


# ===============================================================================
class ZR_obj:
  """Base class for all Zwiftracing data objects.

  Provides common functionality for:
    - HTTP requests to the Zwiftracing API
    - Error handling and logging
    - JSON serialization

  The Zwiftracing API base URL is: https://zwift-ranking.herokuapp.com

  Attributes:
    _client: Shared HTTP client for connection pooling
    _base_url: Base URL for all API requests
  """

  _client: ClassVar[httpx.Client | None] = None
  _base_url: ClassVar[str] = 'https://zwift-ranking.herokuapp.com'

  # -------------------------------------------------------------------------------
  @classmethod
  def get_client(cls) -> httpx.Client:
    """Get or create a shared HTTP client.

    Creates a single shared client for connection pooling across all
    ZR_obj instances. This improves performance when making multiple
    API requests.

    Returns:
      httpx.Client instance configured for Zwiftracing API
    """
    if cls._client is None:
      logger.debug('Creating shared HTTP client for Zwiftracing')
      cls._client = httpx.Client(
        base_url=cls._base_url,
        timeout=30.0,
        follow_redirects=True,
      )
    return cls._client

  # -------------------------------------------------------------------------------
  @classmethod
  def close_client(cls) -> None:
    """Close the shared HTTP client.

    Should be called when done with all ZR_obj operations to ensure
    proper resource cleanup.
    """
    if cls._client is not None:
      logger.debug('Closing shared HTTP client')
      cls._client.close()
      cls._client = None

  # -------------------------------------------------------------------------------
  def fetch_json(
    self,
    endpoint: str,
    method: str = 'GET',
    **kwargs: Any,
  ) -> dict | list:
    """Fetch JSON data from an API endpoint.

    Makes an HTTP request (GET or POST) to the specified endpoint and returns
    the parsed JSON response. Handles errors with proper logging and raises
    ZRNetworkError for any failures.

    Args:
      endpoint: API endpoint path (e.g., '/public/riders/123')
      method: HTTP method ('GET' or 'POST'). Default: 'GET'
      **kwargs: Additional arguments passed to httpx.get() or httpx.post()
        (e.g., headers, params, json, etc.)

    Returns:
      Parsed JSON response (dict or list)

    Raises:
      ZRNetworkError: If the request fails for any reason
        (HTTP error, network error, invalid JSON, etc.)

    Example:
      # GET request
      data = obj.fetch_json('/public/riders/12345')
      # Returns dict with rider data

      # POST request (batch)
      data = obj.fetch_json(
        '/public/riders',
        method='POST',
        headers={'Authorization': 'token'},
        json=[12345, 67890]
      )
      # Returns list of rider dicts
    """
    client = self.get_client()

    try:
      if method.upper() == 'POST':
        response = client.post(endpoint, **kwargs)
      else:
        response = client.get(endpoint, **kwargs)
      response.raise_for_status()
      return response.json()
    except httpx.HTTPStatusError as e:
      logger.error(f'HTTP error {method} {endpoint}: {e.response.status_code}')
      raise ZRNetworkError(
        f'HTTP {e.response.status_code}: {e.response.reason_phrase}',
      ) from e
    except httpx.RequestError as e:
      logger.error(f'Network error {method} {endpoint}: {e}')
      raise ZRNetworkError(f'Network error: {e}') from e
    except json.JSONDecodeError as e:
      logger.error(f'Invalid JSON from {endpoint}: {e}')
      raise ZRNetworkError(f'Invalid JSON response: {e}') from e

  # -------------------------------------------------------------------------------
  def json(self) -> str:
    """Return JSON representation of this object.

    Subclasses should implement to_dict() method to define what gets
    serialized to JSON.

    Returns:
      JSON string with 2-space indentation

    Raises:
      NotImplementedError: If to_dict() is not implemented by subclass
    """
    return json.dumps(self.to_dict(), indent=2)

  # -------------------------------------------------------------------------------
  def to_dict(self) -> dict[str, Any]:
    """Return dictionary representation of this object.

    Subclasses MUST override this method to define the dictionary structure
    for serialization.

    Returns:
      Dictionary representation (excluding private attributes)

    Raises:
      NotImplementedError: Must be overridden by subclass
    """
    raise NotImplementedError('Subclass must implement to_dict()')
