import json
from typing import Any


class ZP_obj:
  """Base class for Zwiftpower data objects.

  Provides common functionality for storing and serializing data fetched
  from Zwiftpower API endpoints. All data classes (Cyclist, Team, Result,
  Signup, Primes, Sprints) inherit from this base class.

  Logging is done via the standard logging module. Configure logging using
  zpdatafetch.logging_config.setup_logging() for detailed output.

  Attributes:
    raw: Dictionary mapping IDs to raw JSON strings from the API
    processed: Dictionary mapping IDs to parsed data dictionaries

  Note:
    The raw attribute stores the original JSON string responses from the
    API before any parsing or validation. Each ID maps to its unprocessed
    JSON string. This ensures we always have access to the exact data
    received for debugging and logging purposes.
  """

  def __init__(self) -> None:
    """Initialize a new ZP_obj instance with empty raw data."""
    self.raw: dict[Any, Any] = {}

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
