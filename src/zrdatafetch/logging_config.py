"""Logging configuration for zrdatafetch.

Provides flexible logging setup that:
- Defaults to ERROR level on stderr (quiet mode)
- Supports optional file logging when configured
- Detects interactive terminal usage for console output
- Allows programmatic configuration via setup_logging()
"""

import logging
import sys
from pathlib import Path

# Default logger for the package
_package_logger: logging.Logger | None = None


def get_logger(name: str) -> logging.Logger:
  """Get a logger instance for the given module name.

  Args:
    name: Module name (typically __name__)

  Returns:
    Configured logger instance
  """
  return logging.getLogger(name)


def setup_logging(
  log_file: str | Path | None = None,
  console_level: str | int = logging.INFO,
  file_level: str | int = logging.DEBUG,
  force_console: bool | None = None,
) -> None:
  """Configure logging for zrdatafetch.

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
    setup_logging(log_file='zrdatafetch.log', console_level='DEBUG')

    # File logging only
    setup_logging(log_file='zrdatafetch.log', force_console=False)

    # Console logging only (interactive mode)
    setup_logging(console_level='INFO')
  """
  # Get the root logger for our package
  logger = logging.getLogger('zrdatafetch')
  logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter

  # Remove existing handlers to avoid duplicates
  logger.handlers.clear()

  # Convert string levels to int if needed
  if isinstance(console_level, str):
    console_level = getattr(logging, console_level.upper())
  if isinstance(file_level, str):
    file_level = getattr(logging, file_level.upper())

  # Determine if we should log to console
  if force_console is None:
    # Auto-detect: use console if stdout is a TTY (interactive)
    use_console = sys.stdout.isatty()
  else:
    use_console = force_console

  # Console handler (if enabled)
  if use_console:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    # Simple format for interactive console - just the message
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

  # File handler (if log_file provided)
  if log_file:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

  # Prevent propagation to root logger
  logger.propagate = False


def _init_default_logging() -> None:
  """Initialize default logging configuration.

  Sets up minimal logging that only shows errors on stderr.
  This is called automatically on module import.
  """
  logger = logging.getLogger('zrdatafetch')
  logger.setLevel(logging.ERROR)

  # Only add stderr handler if no handlers exist
  if not logger.handlers:
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('ERROR: %(message)s')
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)

  logger.propagate = False


# Initialize default logging on import
_init_default_logging()
