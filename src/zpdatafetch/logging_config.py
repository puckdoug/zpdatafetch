"""Logging configuration for zpdatafetch.

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
  """Configure logging for zpdatafetch.

  By default, only errors go to stderr. When configured, this function
  enables more verbose logging to console and/or file.

  Console output uses a simple format (message only) for better readability
  in interactive sessions. File output uses a detailed format with timestamps,
  module names, log levels, and line numbers for debugging.

  Args:
    log_file: Optional path to log file. If None, no file logging occurs.
    console_level: Logging level for console output (default: INFO).
      Can be a string like 'INFO' or an int like logging.INFO.
    file_level: Logging level for file output (default: DEBUG).
      Can be a string like 'DEBUG' or an int like logging.DEBUG.
    force_console: Override TTY detection. If True, always log to console.
      If False, never log to console. If None (default), auto-detect based
      on whether stdout is a TTY.

  Example:
    # Enable console and file logging
    setup_logging(log_file='zpdatafetch.log', console_level='DEBUG')

    # File logging only
    setup_logging(log_file='zpdatafetch.log', force_console=False)

    # Console logging only (interactive mode)
    setup_logging(console_level='INFO')
  """
  setup_logging_for_package(
    'zpdatafetch',
    log_file=log_file,
    console_level=console_level,
    file_level=file_level,
    force_console=force_console,
  )


def _init_default_logging() -> None:
  """Initialize default logging configuration.

  Sets up minimal logging that only shows errors on stderr.
  This is called automatically on module import.
  """
  _init_default_logging_for_package('zpdatafetch')


# Initialize default logging on import
_init_default_logging()
