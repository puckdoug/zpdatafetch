"""Shared JSON parsing utilities."""

import json
import logging

logger = logging.getLogger(__name__)


def parse_json_safe(raw: str, context: str = 'data') -> dict | list:
  """Parse JSON string to Python object with error handling.

  Args:
    raw: Raw JSON string to parse
    context: Description of what's being parsed (for logging)

  Returns:
    Parsed dict or list, or empty dict on parse failure

  Examples:
    >>> parse_json_safe('{"key": "value"}')
    {'key': 'value'}
    >>> parse_json_safe('invalid', 'rider data')
    {}  # logs warning
  """
  if not raw or not raw.strip():
    logger.warning(f'Empty or whitespace-only {context}, returning empty dict')
    return {}

  try:
    result = json.loads(raw)
    logger.debug(f'Successfully parsed {context}')
    return result
  except json.JSONDecodeError as e:
    logger.error(f'Failed to parse {context}: {e}')
    logger.debug(f'Raw data (first 200 chars): {raw[:200]}...')
    return {}
