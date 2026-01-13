"""Zwift rider profile data fetching and management.

Provides access to rider profile information from Zwift's unofficial API
including demographics, statistics, and connected services.
"""

import json
from typing import Any

import httpx

from shared.exceptions import NetworkError
from shared.json_helpers import parse_json_safe
from zdatafetch.auth import ZwiftAuth
from zdatafetch.logging_config import get_logger

logger = get_logger(__name__)


class ZwiftProfile:
  """Fetches and stores Zwift rider profile data.

  Retrieves comprehensive rider information including personal details,
  statistics, connected services, and social data from Zwift's unofficial API.

  API Endpoint: GET https://us-or-rly101.zwift.com/api/profiles/{riderId}
  Documentation: https://github.com/strukturunion-mmw/zwift-api-documentation

  Usage:
      auth = ZwiftAuth(username, password)
      auth.login()

      profile = ZwiftProfile(auth)
      profile.fetch(550564)
      print(profile.json())

  Attributes:
      auth: ZwiftAuth instance for API authentication
      _raw: Dictionary mapping rider IDs to raw JSON response strings
      _fetched: Dictionary mapping rider IDs to parsed profile dictionaries
  """

  BASE_URL = "https://us-or-rly101.zwift.com"

  def __init__(self, auth: ZwiftAuth) -> None:
    """Initialize profile fetcher with auth handler.

    Args:
        auth: Authenticated ZwiftAuth instance
    """
    self.auth = auth
    self._raw: dict[int, str] = {}
    self._fetched: dict[int, dict[str, Any]] = {}

  def fetch(self, *rider_ids: int) -> None:
    """Fetch profile data for one or more riders.

    Args:
        *rider_ids: One or more Zwift rider IDs to fetch

    Raises:
        NetworkError: If API request fails
        RuntimeError: If not authenticated
    """
    for rider_id in rider_ids:
      logger.info(f"Fetching profile for rider {rider_id}")
      self._fetch_single(rider_id)

  def _fetch_single(self, rider_id: int) -> None:
    """Fetch profile data for a single rider.

    Args:
        rider_id: Zwift rider ID

    Raises:
        NetworkError: If API request fails
        RuntimeError: If not authenticated
    """
    url = f"{self.BASE_URL}/api/profiles/{rider_id}"
    token = self.auth.get_access_token()

    headers = {"Authorization": f"Bearer {token}"}

    try:
      with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=30.0)

        if response.status_code == 404:
          raise NetworkError(f"Rider {rider_id} not found")
        if response.status_code != 200:
          raise NetworkError(
            f"Failed to fetch profile for rider {rider_id}: "
            f"HTTP {response.status_code} - {response.text}",
          )

        # Store raw response
        self._raw[rider_id] = response.text

        # Parse and store
        profile_data = parse_json_safe(response.text, rider_id)
        if profile_data:
          self._fetched[rider_id] = profile_data
          logger.debug(f"Profile data retrieved for rider {rider_id}")

    except httpx.TimeoutException as e:
      raise NetworkError(
        f"Request timed out fetching profile for rider {rider_id}: {e}",
      ) from e
    except httpx.HTTPError as e:
      raise NetworkError(
        f"Network error fetching profile for rider {rider_id}: {e}",
      ) from e

  def json(self) -> str:
    """Serialize fetched profile data to formatted JSON string.

    Returns:
        JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)

  def raw(self) -> dict[int, str]:
    """Return the raw response strings.

    Returns:
        Dictionary mapping rider IDs to raw JSON response strings
    """
    return self._raw

  def asdict(self) -> dict[int, dict[str, Any]]:
    """Return fetched profile data as dictionary.

    Returns:
        Dictionary mapping rider IDs to parsed profile dictionaries
    """
    return self._fetched

  def get(self, rider_id: int) -> dict[str, Any] | None:
    """Get profile data for a specific rider.

    Args:
        rider_id: Zwift rider ID

    Returns:
        Profile dictionary for the rider, or None if not fetched
    """
    return self._fetched.get(rider_id)

  def __str__(self) -> str:
    """Return string representation of fetched data.

    Returns:
        String representation of the fetched dictionary
    """
    return str(self._fetched)
