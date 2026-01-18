"""Represents league standings data from Zwiftpower."""

import json
from typing import Any


class ZPLeague:
  """Represents league standings data.

  Wraps league standings data with convenient attribute access.

  Attributes:
    All league data fields are accessible as attributes, including:
    - data: List of rider standings
    - And all other fields from the league data
  """

  def __init__(self, league_data: dict[str, Any] | None = None) -> None:
    """Initialize a ZPLeague from league data dictionary.

    Args:
      league_data: Dictionary containing league standings data.
                   If None, creates an empty league object.
    """
    self._data = league_data if league_data is not None else {}

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to league data fields.

    Args:
      name: Field name to access

    Returns:
      Value of the field

    Raises:
      AttributeError: If field doesn't exist
    """
    if name.startswith('_'):
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    try:
      return self._data[name]
    except KeyError:
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to league data.

    Args:
      key: Field name to access

    Returns:
      Value of the field
    """
    return self._data[key]

  def __repr__(self) -> str:
    """Return detailed representation showing all league data.

    Returns:
      String in format: ZPLeague(key=value, key=value, ...)
    """
    items = ', '.join(f'{k}={v!r}' for k, v in self._data.items())
    return f'ZPLeague({items})'

  def __str__(self) -> str:
    """Return human-readable string with all league data.

    Returns:
      Multi-line string showing all fields
    """
    lines = ['ZPLeague(']
    for key, value in self._data.items():
      lines.append(f'  {key}={value!r},')
    lines.append(')')
    return '\n'.join(lines)

  def asdict(self) -> dict[str, Any]:
    """Return the underlying league data as a dictionary.

    Returns:
      Dictionary containing all league data
    """
    return self._data

  def json(self) -> str:
    """Return JSON representation of league data.

    Returns:
      JSON string of league data
    """
    return json.dumps(self._data, indent=2)
