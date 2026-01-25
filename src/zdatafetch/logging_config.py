"""Logging configuration for zdatafetch.

Provides centralized logging setup and logger retrieval for the package.
"""

import logging


def setup_logging(
  verbose: bool = False,
  log_file: str | None = None,
  console_level: int = logging.INFO,
  force_console: bool = True,
) -> None:
  """Configure logging for zdatafetch package.

  Args:
      verbose: If True, set log level to DEBUG; otherwise INFO (deprecated, use console_level)
      log_file: Optional path to log file
      console_level: Logging level for console output
      force_console: If True, always log to console even if log_file is set
  """
  # Handle legacy verbose parameter
  if verbose:
    console_level = logging.DEBUG

  # Configure basic logging
  if log_file and not force_console:
    # Log to file only
    logging.basicConfig(
      level=console_level,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
      filename=log_file,
      filemode='a',
    )
  else:
    # Log to console
    logging.basicConfig(
      level=console_level,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S',
    )

  # If both file and console are needed, add file handler separately
  if log_file and force_console:
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(console_level)
    file_handler.setFormatter(
      logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
      ),
    )
    logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
  """Get a logger instance for the given name.

  Args:
      name: Logger name (typically __name__ from calling module)

  Returns:
      Logger instance
  """
  return logging.getLogger(name)
