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
    _raw: Dictionary mapping IDs to raw JSON strings from the API (response.text)
    _fetched: Dictionary mapping IDs to parsed data dictionaries
    processed: Dictionary reserved for future processing functionality

  Note:
    The _raw attribute stores the original JSON string responses from the
    API (response.text) before any parsing or validation. Each ID maps to
    its unprocessed JSON string. The _fetched attribute contains the parsed
    Python dictionaries. The processed attribute is reserved for future use.
  """

  def __init__(self) -> None:
    """Initialize a new ZP_obj instance with empty data structures."""
    self._raw: dict[int, str] = {}  # True raw response.text strings
    self._fetched: dict[int, dict] = {}  # Parsed Python dicts
    self.processed: dict[int, dict] = {}  # Reserved for future processing

  def __str__(self) -> str:
    """Return string representation of the fetched data.

    Returns:
      String representation of the fetched dictionary
    """
    return str(self._fetched)

  def json(self) -> str:
    """Serialize the fetched data to formatted JSON string.

    Returns:
      JSON string with 2-space indentation (clean, single-encoded)
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)

  def asdict(self) -> dict[Any, Any]:
    """Return the fetched data as a dictionary.

    Returns:
      Dictionary containing all fetched/parsed data from the API
    """
    return self._fetched

  def raw(self) -> dict[int, str]:
    """Return the true raw response strings.

    Returns:
      Dictionary mapping IDs to raw response.text strings
    """
    return self._raw

  def fetched(self) -> dict[int, dict]:
    """Return the parsed/fetched data.

    Returns:
      Dictionary mapping IDs to parsed data dictionaries
    """
    return self._fetched
