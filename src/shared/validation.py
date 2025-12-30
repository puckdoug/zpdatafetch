"""Input validation utilities for zpdatafetch and zrdatafetch.

ID Ranges:
----------
- Zwift IDs: 1 to sys.maxsize
- Race IDs: 1 to sys.maxsize
- Team IDs: 1 to sys.maxsize
- Epoch: -1 (current) or 0 to 2,147,483,647 (Unix timestamp)

Batch Limits:
-------------
- Maximum 1000 IDs per batch request

These ranges are based on Python's native integer limits and observed
API behavior.
"""

import sys
from typing import Literal

# ID Range Constants
# Use sys.maxsize (not hardcoded values) for maximum ID bounds
# This is Python's native maximum integer size (2^63-1 on 64-bit systems)
ZWIFT_ID_MIN = 1
ZWIFT_ID_MAX = sys.maxsize
RACE_ID_MIN = 1
RACE_ID_MAX = sys.maxsize
TEAM_ID_MIN = 1
TEAM_ID_MAX = sys.maxsize
LEAGUE_ID_MIN = 1
LEAGUE_ID_MAX = sys.maxsize
EPOCH_MIN = -1  # -1 means "current epoch"
EPOCH_MAX = 2147483647  # Max 32-bit timestamp (2038-01-19)

# Batch Limits
MAX_BATCH_SIZE = 1000


class ValidationError(ValueError):
  """Raised when input validation fails."""


def validate_zwift_id(
  value: int | str,
  allow_zero: bool = False,
) -> int:
  """Validate a Zwift ID.

  Args:
      value: ID to validate (int or string)
      allow_zero: If True, allow zwift_id=0 (for dataclass defaults)

  Returns:
      Validated integer ID

  Raises:
      ValidationError: If ID is invalid
  """
  try:
    id_int = int(value) if not isinstance(value, int) else value
  except (ValueError, TypeError) as e:
    raise ValidationError(
      f"Invalid Zwift ID '{value}': must be an integer",
    ) from e

  min_val = 0 if allow_zero else ZWIFT_ID_MIN
  if not (min_val <= id_int <= ZWIFT_ID_MAX):
    raise ValidationError(
      f'Invalid Zwift ID {id_int}: must be between {min_val} and {ZWIFT_ID_MAX}',
    )

  return id_int


def validate_race_id(value: int | str) -> int:
  """Validate a race ID.

  Args:
      value: ID to validate (int or string)

  Returns:
      Validated integer ID

  Raises:
      ValidationError: If ID is invalid
  """
  try:
    id_int = int(value) if not isinstance(value, int) else value
  except (ValueError, TypeError) as e:
    raise ValidationError(
      f"Invalid race ID '{value}': must be an integer",
    ) from e

  if not (RACE_ID_MIN <= id_int <= RACE_ID_MAX):
    raise ValidationError(
      f'Invalid race ID {id_int}: must be between {RACE_ID_MIN} and {RACE_ID_MAX}',
    )

  return id_int


def validate_team_id(value: int | str) -> int:
  """Validate a team ID.

  Args:
      value: ID to validate (int or string)

  Returns:
      Validated integer ID

  Raises:
      ValidationError: If ID is invalid
  """
  try:
    id_int = int(value) if not isinstance(value, int) else value
  except (ValueError, TypeError) as e:
    raise ValidationError(
      f"Invalid team ID '{value}': must be an integer",
    ) from e

  if not (TEAM_ID_MIN <= id_int <= TEAM_ID_MAX):
    raise ValidationError(
      f'Invalid team ID {id_int}: must be between '
      f'{TEAM_ID_MIN} and {TEAM_ID_MAX}',
    )

  return id_int


def validate_league_id(value: int | str) -> int:
  """Validate a league ID.

  Args:
      value: ID to validate (int or string)

  Returns:
      Validated integer ID

  Raises:
      ValidationError: If ID is invalid
  """
  try:
    id_int = int(value) if not isinstance(value, int) else value
  except (ValueError, TypeError) as e:
    raise ValidationError(
      f"Invalid league ID '{value}': must be an integer",
    ) from e

  if not (LEAGUE_ID_MIN <= id_int <= LEAGUE_ID_MAX):
    raise ValidationError(
      f'Invalid league ID {id_int}: must be between '
      f'{LEAGUE_ID_MIN} and {LEAGUE_ID_MAX}',
    )

  return id_int


def validate_epoch(value: int) -> int:
  """Validate an epoch parameter.

  Args:
      value: Epoch timestamp or -1 for current

  Returns:
      Validated epoch

  Raises:
      ValidationError: If epoch is invalid
  """
  if value == -1:
    return value  # Special value meaning "current epoch"

  if not (0 <= value <= EPOCH_MAX):
    raise ValidationError(
      f'Invalid epoch {value}: must be -1 or between 0 and {EPOCH_MAX}',
    )

  return value


def validate_batch_size(count: int, max_size: int = MAX_BATCH_SIZE) -> None:
  """Validate batch request size.

  Args:
      count: Number of IDs in batch
      max_size: Maximum allowed batch size

  Raises:
      ValidationError: If batch is too large
  """
  if count > max_size:
    raise ValidationError(
      f'Batch size {count} exceeds maximum of {max_size}',
    )


def validate_id_list(
  ids: list[int | str],
  id_type: Literal['zwift', 'race', 'team', 'league'] = 'zwift',
) -> list[int]:
  """Validate a list of IDs.

  Args:
      ids: List of IDs to validate
      id_type: Type of ID ('zwift', 'race', 'team', or 'league')

  Returns:
      List of validated integer IDs

  Raises:
      ValidationError: If any ID is invalid
  """
  validators = {
    'zwift': validate_zwift_id,
    'race': validate_race_id,
    'team': validate_team_id,
    'league': validate_league_id,
  }

  validator = validators[id_type]
  validated = []

  for i, id_val in enumerate(ids, 1):
    try:
      validated.append(validator(id_val))
    except ValidationError as e:
      # Add position info to error message
      raise ValidationError(f'ID at position {i}: {e}') from e

  return validated
