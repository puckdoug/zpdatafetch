"""Zwift follower/followee data fetching (not yet implemented).

Placeholder for future implementation of follower/followee data retrieval.
"""

from zdatafetch.auth import ZwiftAuth


class ZwiftFollowers:
  """Fetches Zwift follower and followee data.

  NOT YET IMPLEMENTED - Placeholder for future functionality.

  Future API Endpoints:
      - GET /api/profiles/{riderId}/followers
      - GET /api/profiles/{riderId}/followees
  """

  def __init__(self, auth: ZwiftAuth) -> None:
    """Initialize followers fetcher with auth handler.

    Args:
        auth: Authenticated ZwiftAuth instance
    """
    self.auth = auth
    self._raw: dict[int, str] = {}
    self._fetched: dict[int, dict] = {}

  def fetch(self, *rider_ids: int) -> None:
    """Fetch follower data for one or more riders.

    Args:
        *rider_ids: One or more Zwift rider IDs to fetch

    Raises:
        NotImplementedError: This functionality is not yet implemented
    """
    raise NotImplementedError(
      'Follower fetching is not yet implemented. Coming soon!',
    )
