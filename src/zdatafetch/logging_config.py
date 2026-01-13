"""Logging configuration for zdatafetch.

Provides centralized logging setup and logger retrieval for the package.
"""

import logging


def setup_logging(verbose: bool = False) -> None:
  """Configure logging for zdatafetch package.

  Args:
      verbose: If True, set log level to DEBUG; otherwise INFO
  """
  level = logging.DEBUG if verbose else logging.INFO
  logging.basicConfig(
    level=level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
  )


def get_logger(name: str) -> logging.Logger:
  """Get a logger instance for the given name.

  Args:
      name: Logger name (typically __name__ from calling module)

  Returns:
      Logger instance
  """
  return logging.getLogger(name)
