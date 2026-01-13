"""Zwift RideOn data fetching (not yet implemented).

Placeholder for future implementation of RideOn data retrieval.
"""

from zdatafetch.auth import ZwiftAuth


class ZwiftRideOns:
  """Fetches Zwift RideOn data.

  NOT YET IMPLEMENTED - Placeholder for future functionality.

  Future API Endpoints:
      - GET /api/rideons/{activityId}
      - POST /api/rideons - Give RideOn
  """

  def __init__(self, auth: ZwiftAuth) -> None:
    """Initialize RideOns fetcher with auth handler.

    Args:
        auth: Authenticated ZwiftAuth instance
    """
    self.auth = auth
    self._raw: dict[int, str] = {}
    self._fetched: dict[int, dict] = {}

  def fetch(self, *activity_ids: int) -> None:
    """Fetch RideOn data for one or more activities.

    Args:
        *activity_ids: One or more activity IDs to fetch

    Raises:
        NotImplementedError: This functionality is not yet implemented
    """
    raise NotImplementedError(
      'RideOn fetching is not yet implemented. Coming soon!',
    )
