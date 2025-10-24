import json
from typing import Any, Dict


class ZP_obj:
  """Base class for Zwiftpower data objects.

  Provides common functionality for storing and serializing data fetched
  from Zwiftpower API endpoints. All data classes (Cyclist, Team, Result,
  Signup, Primes) inherit from this base class.

  Attributes:
    raw: Dictionary containing the raw data from the API
    verbose: Enable verbose output for debugging
  """

  def __init__(self) -> None:
    """Initialize a new ZP_obj instance with empty raw data."""
    self.raw: dict[Any, Any] = {}
    self.verbose: bool = False

  def __str__(self) -> str:
    """Return string representation of the raw data.

    Returns:
      String representation of the raw dictionary
    """
    return str(self.raw)

  def json(self) -> str:
    """Serialize the raw data to formatted JSON string.

    Returns:
      JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self.raw)

  def asdict(self) -> dict[Any, Any]:
    """Return the raw data as a dictionary.

    Returns:
      Dictionary containing all raw data from the API
    """
    return self.raw
