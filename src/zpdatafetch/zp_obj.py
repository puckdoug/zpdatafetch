import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
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

  # Private attributes (not in __init__ by default, but included for dataclass)
  _raw: dict[int, str] = field(default_factory=dict, repr=False)
  _fetched: dict[int, Any] = field(default_factory=dict, repr=False)
  processed: dict[int, Any] = field(default_factory=dict, repr=False)

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

  def fetched(self) -> dict[int, Any]:
    """Return the parsed/fetched data.

    Returns:
      Dictionary mapping IDs to parsed data dictionaries
    """
    return self._fetched
