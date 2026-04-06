"""Logging configuration for zsdatafetch.

Provides flexible logging setup that:
- Defaults to ERROR level on stderr (quiet mode)
- Supports optional file logging when configured
- Detects interactive terminal usage for console output
- Allows programmatic configuration via setup_logging()
"""

import logging
from pathlib import Path

from shared.logging import (
  _init_default_logging_for_package,
  get_logger,
  setup_logging_for_package,
)

__all__ = [
  'get_logger',
  'setup_logging',
]


def setup_logging(
  log_file: str | Path | None = None,
  console_level: str | int = logging.INFO,
  file_level: str | int = logging.DEBUG,
  force_console: bool | None = None,
) -> None:
  """Configure logging for zsdatafetch.

  Args:
    log_file: Optional path to log file.
    console_level: Logging level for console output.
    file_level: Logging level for file output.
    force_console: Override TTY detection.
  """
  setup_logging_for_package(
    'zsdatafetch',
    log_file=log_file,
    console_level=console_level,
    file_level=file_level,
    force_console=force_console,
  )


def _init_default_logging() -> None:
  """Initialize default logging configuration."""
  _init_default_logging_for_package('zsdatafetch')


# Initialize default logging on import
_init_default_logging()
