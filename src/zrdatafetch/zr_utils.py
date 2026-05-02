"""Utility functions for Zwiftracing data transformations.

Provides common data conversion functions used across ZR dataclasses:
- Safe type conversions (int, float, str)
- Nested dictionary value extraction
"""

from typing import Any


def safe_int(value: Any, default: int = 0) -> int:  # noqa: ANN401
  """Safely convert value to integer.

  String inputs have US-locale thousands separators (commas) stripped before
  conversion, so values like ``'7,200'`` parse correctly.

  Args:
    value: Value to convert
    default: Default value if conversion fails (default: 0)

  Returns:
    Integer value or default if conversion fails
  """
  if value is None:
    return default
  if isinstance(value, str):
    value = value.replace(',', '')
  try:
    return int(value)
  except (ValueError, TypeError):
    return default


def safe_float(value: Any, default: float = 0.0) -> float:  # noqa: ANN401
  """Safely convert value to float.

  String inputs have US-locale thousands separators (commas) stripped before
  conversion, so values like ``'7,200.0'`` parse correctly. Decimal-comma
  inputs (e.g. European ``'7,2'`` meaning 7.2) are not supported and will
  fall back to ``default``.

  Args:
    value: Value to convert
    default: Default value if conversion fails (default: 0.0)

  Returns:
    Float value or default if conversion fails
  """
  if value is None:
    return default
  if isinstance(value, str):
    value = value.replace(',', '')
  try:
    return float(value)
  except (ValueError, TypeError):
    return default


def safe_str(value: Any, default: str = '') -> str:  # noqa: ANN401
  """Safely convert value to string.

  Args:
    value: Value to convert
    default: Default value if None (default: empty string)

  Returns:
    String value or default if None
  """
  if value is None:
    return default
  return str(value)


def extract_nested_value(
  data: dict[str, Any],
  *keys: str,
  default: Any = None,  # noqa: ANN401
) -> Any:  # noqa: ANN401
  """Extract value from nested dictionary using dot notation.

  Safely traverses nested dictionaries without raising KeyError.

  Args:
    data: Dictionary to extract from
    *keys: Keys to traverse (e.g., 'race', 'current', 'rating')
    default: Default value if path doesn't exist (default: None)

  Returns:
    Value at the specified path or default if not found

  Examples:
    >>> data = {'race': {'current': {'rating': 2250.0}}}
    >>> extract_nested_value(data, 'race', 'current', 'rating')
    2250.0
    >>> extract_nested_value(data, 'race', 'max90', 'rating', default=0.0)
    0.0
  """
  current = data
  for key in keys:
    if not isinstance(current, dict):
      return default
    current = current.get(key)
    if current is None:
      return default
  return current
