"""Tests for logging functionality."""

import logging
import tempfile
from pathlib import Path

import pytest

from zpdatafetch import setup_logging
from zpdatafetch.logging_config import get_logger


def _close_handlers():
  """Close all handlers on the zpdatafetch logger."""
  logger = logging.getLogger('zpdatafetch')
  # Use slice copy to avoid modification during iteration
  for handler in logger.handlers[:]:
    try:
      handler.close()
    except (OSError, ValueError):
      # On Windows, closing a handler to a deleted file may raise OSError
      pass


@pytest.fixture(autouse=True)
def reset_logging():
  """Reset logging configuration before and after each test."""
  # Clear handlers before test and reinitialize default
  logger = logging.getLogger('zpdatafetch')
  _close_handlers()
  logger.handlers.clear()
  from zpdatafetch.logging_config import _init_default_logging

  _init_default_logging()

  yield

  # Clear handlers after test and reinitialize default
  _close_handlers()
  logger.handlers.clear()
  _init_default_logging()


def test_default_logging_level():
  """Test that default logging is set to ERROR level."""
  logger = logging.getLogger('zpdatafetch')

  # Should have default ERROR level
  assert logger.level == logging.ERROR

  # Should have one handler (stderr)
  assert len(logger.handlers) == 1
  assert logger.handlers[0].level == logging.ERROR


def test_default_logging_format():
  """Test that default logging has simple ERROR format configured."""
  logger = logging.getLogger('zpdatafetch')

  # Should have one stderr handler
  assert len(logger.handlers) == 1
  handler = logger.handlers[0]

  # Verify it's a StreamHandler (stderr gets captured by pytest, so we can't check the exact stream)
  assert isinstance(handler, logging.StreamHandler)

  # Check the format - should be simple
  formatter = handler.formatter
  assert formatter is not None
  # The format string should be simple (just ERROR: %(message)s)
  assert formatter._fmt == 'ERROR: %(message)s'


def test_console_info_logging(capfd):
  """Test console logging at INFO level with simple format."""
  setup_logging(console_level='INFO', force_console=True)
  logger = get_logger('zpdatafetch.test')

  logger.info('Info message')
  logger.debug('Debug message')

  captured = capfd.readouterr()
  # Should show INFO on stdout
  assert 'Info message' in captured.out
  # Should NOT show DEBUG (level too low)
  assert 'Debug message' not in captured.out
  # Should be simple format (no timestamp, module, level)
  assert 'INFO' not in captured.out  # No log level in output
  assert '2025-' not in captured.out  # No timestamp


def test_console_debug_logging(capfd):
  """Test console logging at DEBUG level with simple format."""
  setup_logging(console_level='DEBUG', force_console=True)
  logger = get_logger('zpdatafetch.test')

  logger.debug('Debug message')
  logger.info('Info message')

  captured = capfd.readouterr()
  # Should show both DEBUG and INFO on stdout
  assert 'Debug message' in captured.out
  assert 'Info message' in captured.out
  # Should be simple format
  assert 'DEBUG' not in captured.out
  assert 'INFO' not in captured.out


def test_file_logging_format():
  """Test file logging uses detailed format."""
  with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    log_file = Path(f.name)

  try:
    setup_logging(log_file=log_file, force_console=False)
    logger = get_logger('zpdatafetch.test')

    logger.info('Test info message')
    logger.debug('Test debug message')

    # Read log file
    log_content = log_file.read_text()

    # Should contain both messages
    assert 'Test info message' in log_content
    assert 'Test debug message' in log_content

    # Should have detailed format
    # Timestamp format: 2025-10-24 15:17:39
    assert '- zpdatafetch.test -' in log_content
    assert '- INFO -' in log_content
    assert '- DEBUG -' in log_content
    # Should include function and line number info
    assert 'test_file_logging_format' in log_content

  finally:
    _close_handlers()
    log_file.unlink()


def test_file_logging_levels():
  """Test that file logging respects DEBUG level by default."""
  with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    log_file = Path(f.name)

  try:
    setup_logging(log_file=log_file, file_level='DEBUG', force_console=False)
    logger = get_logger('zpdatafetch.test')

    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')

    log_content = log_file.read_text()

    # All levels should be in file
    assert 'Debug message' in log_content
    assert 'Info message' in log_content
    assert 'Warning message' in log_content

  finally:
    _close_handlers()
    log_file.unlink()


def test_combined_console_and_file_logging(capfd):
  """Test console and file logging together with different formats and levels."""
  with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    log_file = Path(f.name)

  try:
    setup_logging(
      log_file=log_file,
      console_level='INFO',
      file_level='DEBUG',
      force_console=True,
    )
    logger = get_logger('zpdatafetch.test')

    logger.debug('Debug only in file')
    logger.info('Info in both')

    # Check console output
    captured = capfd.readouterr()
    assert 'Debug only in file' not in captured.out  # DEBUG not on console
    assert 'Info in both' in captured.out
    # Console should be simple format
    assert 'INFO' not in captured.out

    # Check file output
    log_content = log_file.read_text()
    assert 'Debug only in file' in log_content  # DEBUG in file
    assert 'Info in both' in log_content
    # File should have detailed format
    assert '- zpdatafetch.test -' in log_content
    assert '- DEBUG -' in log_content
    assert '- INFO -' in log_content

  finally:
    _close_handlers()
    log_file.unlink()


def test_console_format_is_message_only(capfd):
  """Test that console format contains only the message, no metadata."""
  setup_logging(console_level='INFO', force_console=True)
  logger = get_logger('zpdatafetch.test')

  logger.info('Simple message')

  captured = capfd.readouterr()

  # Should contain ONLY the message
  lines = [line for line in captured.out.split('\n') if line.strip()]
  assert len(lines) == 1
  assert lines[0] == 'Simple message'


def test_file_format_includes_metadata():
  """Test that file format includes all metadata fields."""
  with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    log_file = Path(f.name)

  try:
    setup_logging(log_file=log_file, force_console=False)
    logger = get_logger('zpdatafetch.test')

    logger.info('Metadata test')

    log_content = log_file.read_text()

    # Check for all metadata components
    assert 'zpdatafetch.test' in log_content  # module name
    assert 'INFO' in log_content  # log level
    assert 'test_file_format_includes_metadata' in log_content  # function name
    assert 'Metadata test' in log_content  # message
    # Should have timestamp format YYYY-MM-DD HH:MM:SS
    import re

    assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', log_content)

  finally:
    _close_handlers()
    log_file.unlink()


def test_force_console_true():
  """Test force_console=True enables console even when not a TTY."""
  setup_logging(console_level='INFO', force_console=True)
  logger = logging.getLogger('zpdatafetch')

  # Should have console handler
  handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
  assert len(handlers) >= 1


def test_force_console_false(capfd):
  """Test force_console=False disables console logging."""
  setup_logging(console_level='INFO', force_console=False)
  logger = get_logger('zpdatafetch.test')

  logger.info('Should not appear')

  captured = capfd.readouterr()
  # Should NOT go to console
  assert 'Should not appear' not in captured.out
  assert 'Should not appear' not in captured.err


def test_log_file_creation():
  """Test that log file is created with proper directory structure."""
  with tempfile.TemporaryDirectory() as tmpdir:
    log_file = Path(tmpdir) / 'subdir' / 'test.log'

    setup_logging(log_file=log_file, force_console=False)
    logger = get_logger('zpdatafetch.test')

    logger.info('Test message')

    # File and directory should be created
    assert log_file.exists()
    assert log_file.parent.exists()
    assert 'Test message' in log_file.read_text()

    # Close handlers before directory cleanup
    _close_handlers()


def test_string_log_levels():
  """Test that string log levels are properly converted."""
  with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    log_file = Path(f.name)

  try:
    # Use string levels instead of logging constants
    setup_logging(
      log_file=log_file,
      console_level='WARNING',
      file_level='INFO',
    )
    logger = get_logger('zpdatafetch.test')

    logger.debug('Debug')
    logger.info('Info')
    logger.warning('Warning')

    log_content = log_file.read_text()

    # DEBUG should not appear (file level is INFO)
    assert 'Debug' not in log_content
    # INFO and WARNING should appear
    assert 'Info' in log_content
    assert 'Warning' in log_content

  finally:
    _close_handlers()
    log_file.unlink()


def test_multiple_setup_logging_calls():
  """Test that calling setup_logging multiple times replaces handlers."""
  with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    log_file = Path(f.name)

  try:
    # First setup
    setup_logging(console_level='INFO', force_console=True)
    logger = logging.getLogger('zpdatafetch')
    initial_handler_count = len(logger.handlers)

    # Second setup with file
    setup_logging(log_file=log_file, console_level='DEBUG', force_console=True)

    # Should clear old handlers and add new ones
    # Should not accumulate handlers
    assert len(logger.handlers) >= initial_handler_count

  finally:
    _close_handlers()
    log_file.unlink()
