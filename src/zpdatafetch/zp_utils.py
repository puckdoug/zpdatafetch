"""Utility functions for ZwiftPower data transformations.

Provides common data conversion functions used across ZP dataclasses:
- Category conversion (numeric division to letter)
- Gender conversion (numeric to string)
- Time formatting (seconds to hh:mm:ss.sss)
- Timestamp conversion (Unix to ISO-8601)
- Array field extraction (from [value, flag] format)
"""

from datetime import datetime, timezone
from typing import Any


def set_rider_category(div: int) -> str:
  """Convert numeric division to rider category letter.

  Maps ZwiftPower numeric division codes to category letters:
  - 0 → empty string (no division)
  - 10 → A
  - 20 → B
  - 30 → C
  - 40 → D
  - Other values → string representation of the value

  Args:
      div: Numeric division code from API

  Returns:
      Category letter (A-D) or empty string for no division
  """
  match div:
    case 0:
      return ''
    case 10:
      return 'A'
    case 20:
      return 'B'
    case 30:
      return 'C'
    case 40:
      return 'D'
    case _:
      return str(div)


def convert_gender(male: int) -> str:
  """Convert numeric gender code to readable gender string.

  Maps ZwiftPower gender codes:
  - 1 → 'male'
  - 0 → 'female'
  - Other values → empty string

  Args:
      male: Numeric gender code from API

  Returns:
      Gender string ('male', 'female', or empty)
  """
  match male:
    case 1:
      return 'male'
    case 0:
      return 'female'
    case _:
      return ''


def format_time_hms(seconds: float) -> str:
  """Format time in seconds to hh:mm:ss.sss format.

  Args:
      seconds: Time in seconds (can include fractional seconds)

  Returns:
      Formatted string in hh:mm:ss.sss format, or empty string if no seconds
  """
  if not seconds:
    return ''
  seconds = float(seconds)
  hours = int(seconds // 3600)
  remaining = seconds % 3600
  minutes = int(remaining // 60)
  secs = remaining % 60
  return f'{hours:02d}:{minutes:02d}:{secs:06.3f}'


def convert_timestamp_to_iso8601(timestamp: float | str) -> str:
  """Convert Unix timestamp to ISO-8601 UTC format.

  Args:
      timestamp: Unix timestamp (seconds since epoch) or already-formatted string

  Returns:
      ISO-8601 formatted string in UTC (e.g., '2025-12-03T22:10:00Z'),
      or empty string if no timestamp
  """
  if not timestamp:
    return ''

  # If already a string, assume it's already in ISO format
  if isinstance(timestamp, str):
    return timestamp

  try:
    dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    return dt.isoformat().replace('+00:00', 'Z')
  except (ValueError, OSError, TypeError):
    return ''


def extract_value(value: Any, default: Any = None) -> Any:
  """Extract value from [value, flag] format or return as-is.

  Many ZwiftPower API fields are returned as [value, flag] arrays
  where only the first element is needed.

  Args:
      value: Value that may be a list or scalar
      default: Default value if extraction fails

  Returns:
      First element if list, otherwise the value itself
  """
  if isinstance(value, list) and len(value) > 0:
    return value[0]
  return value if value is not None else default


def extract_numeric(value: Any, type_func: type, default: Any) -> Any:
  """Extract and convert numeric value, handling array format.

  Args:
      value: Value that may be a list or scalar
      type_func: Type conversion function (int, float)
      default: Default value if conversion fails

  Returns:
      Converted numeric value or default
  """
  extracted = extract_value(value, default)
  if extracted == default:
    return default
  try:
    return type_func(extracted)
  except (ValueError, TypeError):
    return default
