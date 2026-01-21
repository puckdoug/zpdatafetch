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
  - 5 → A+ (pro/elite)
  - 10 → A
  - 20 → B
  - 30 → C
  - 40 → D
  - Other values → string representation of the value

  Args:
      div: Numeric division code from API

  Returns:
      Category letter (A+/A-D) or empty string for no division
  """
  match div:
    case 0:
      return ''
    case 5:
      return 'A+'
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


def convert_label_to_pen(label: int) -> str:
  """Convert numeric label to race pen (category) letter.

  Maps ZwiftPower race-specific pen/category labels to letters:
  - 1 → A
  - 2 → B
  - 3 → C
  - 4 → D
  - 5 → E
  - Other values → empty string

  Args:
      label: Numeric label code from API (race-specific category assignment)

  Returns:
      Pen letter (A-E) or empty string for no label
  """
  match label:
    case 1:
      return 'A'
    case 2:
      return 'B'
    case 3:
      return 'C'
    case 4:
      return 'D'
    case 5:
      return 'E'
    case _:
      return ''


def convert_gender(gender_value: int | str) -> str:
  """Convert gender code to readable gender string.

  Maps ZwiftPower gender codes from either numeric or string format:
  - 1 or 'm' → 'male'
  - 0 or 'f' → 'female'
  - Other values → empty string

  Args:
      gender_value: Gender code from API (numeric 0/1 or string 'm'/'f')

  Returns:
      Gender string ('male', 'female', or empty)
  """
  match gender_value:
    case 1 | 'm' | 'M':
      return 'male'
    case 0 | 'f' | 'F':
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


def convert_msec_to_iso8601(msec: int) -> str:
  """Convert milliseconds since epoch to ISO-8601 format with milliseconds.

  Args:
      msec: Milliseconds since epoch (Unix timestamp in milliseconds)

  Returns:
      ISO-8601 formatted datetime string with milliseconds,
      e.g., '2024-01-15T14:30:45.123Z', or empty string if no value
  """
  if not msec:
    return ''
  try:
    # Convert milliseconds to seconds and microseconds
    seconds = msec // 1000
    microseconds = (msec % 1000) * 1000
    # Create datetime from Unix timestamp
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    # Replace microseconds and format as ISO8601 with 'Z' suffix
    dt = dt.replace(microsecond=microseconds)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
  except (ValueError, OSError, TypeError, OverflowError):
    return ''


def convert_iso8601_to_msec(iso_str: str) -> int:
  """Convert ISO-8601 datetime string back to milliseconds since epoch.

  Args:
      iso_str: ISO-8601 formatted datetime string, e.g., '2024-01-15T14:30:45.123Z'

  Returns:
      Milliseconds since epoch (Unix timestamp in milliseconds),
      or 0 if conversion fails
  """
  if not iso_str:
    return 0
  try:
    # Remove 'Z' suffix if present and replace with timezone offset
    if iso_str.endswith('Z'):
      iso_str = iso_str[:-1] + '+00:00'
    dt = datetime.fromisoformat(iso_str)
    # Convert to milliseconds since epoch
    return int(dt.timestamp() * 1000)
  except (ValueError, OSError, TypeError):
    return 0


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
