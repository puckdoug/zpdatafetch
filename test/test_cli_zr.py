"""Tests for zrdatafetch CLI module.

Tests the command-line interface including argument parsing and command
routing.
"""

from unittest.mock import MagicMock, patch

import pytest

from zrdatafetch.cli import main


# ===============================================================================
class TestCLIArgumentParsing:
  """Test CLI argument parsing."""

  def test_main_with_no_args(self, capsys):
    """Test main with no arguments (should print help or exit gracefully)."""
    with patch('sys.argv', ['zrdata']):
      result = main()
      # Should return None on success (no command specified)
      assert result is None

  def test_main_with_verbose_flag(self, capsys):
    """Test main with verbose flag."""
    with patch('sys.argv', ['zrdata', '-v']):
      result = main()
      assert result is None

  def test_main_with_debug_flag(self, capsys):
    """Test main with debug flag."""
    with patch('sys.argv', ['zrdata', '-vv']):
      result = main()
      assert result is None

  def test_main_with_log_file(self, tmp_path, capsys):
    """Test main with log file argument."""
    log_file = tmp_path / 'test.log'
    with patch('sys.argv', ['zrdata', '--log-file', str(log_file)]):
      result = main()
      assert result is None

  def test_main_with_raw_flag(self):
    """Test main with raw flag."""
    with patch('sys.argv', ['zrdata', '-r']):
      result = main()
      assert result is None

  def test_main_with_rating_command(self):
    """Test main with rating command."""
    with patch('sys.argv', ['zrdata', 'rating', '12345']):
      result = main()
      assert result is None

  def test_main_with_result_command(self):
    """Test main with result command."""
    with patch('sys.argv', ['zrdata', 'result', '3590800']):
      result = main()
      assert result is None

  def test_main_with_team_command(self):
    """Test main with team command."""
    with patch('sys.argv', ['zrdata', 'team', '456']):
      result = main()
      assert result is None

  def test_main_with_multiple_ids(self):
    """Test main with multiple IDs."""
    with patch('sys.argv', ['zrdata', 'rating', '12345', '67890', '11111']):
      result = main()
      assert result is None

  def test_main_with_invalid_command(self):
    """Test main with invalid command."""
    with patch('sys.argv', ['zrdata', 'invalid']):
      # ArgumentParser will exit with error, so we need to catch it
      with pytest.raises(SystemExit):
        main()


# ===============================================================================
class TestCLILoggingConfiguration:
  """Test logging configuration in CLI."""

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_debug_level(self, mock_setup):
    """Test that debug flag sets DEBUG level logging."""
    import logging

    with patch('sys.argv', ['zrdata', '-vv', 'rating', '123']):
      main()
      # setup_logging should be called with DEBUG level
      mock_setup.assert_called_once()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('console_level') == logging.DEBUG

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_verbose_level(self, mock_setup):
    """Test that verbose flag sets INFO level logging."""
    import logging

    with patch('sys.argv', ['zrdata', '-v', 'rating', '123']):
      main()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('console_level') == logging.INFO

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_with_file_only(self, mock_setup):
    """Test that log file sets force_console=False."""
    with patch('sys.argv', ['zrdata', '--log-file', 'test.log', 'rating', '123']):
      main()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('force_console') is False

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_debug_with_file(self, mock_setup):
    """Test debug flag with log file."""
    import logging

    with patch(
      'sys.argv', ['zrdata', '-vv', '--log-file', 'test.log', 'rating', '123']
    ):
      main()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('console_level') == logging.DEBUG
      assert call_kwargs.get('log_file') == 'test.log'


# ===============================================================================
class TestCLICommandRouting:
  """Test command routing logic (placeholder tests).

  These tests verify that the CLI structure is correct.
  Actual command implementations will be added when classes are refactored.
  """

  def test_cli_handles_rating_command(self):
    """Test that CLI accepts rating command."""
    # This should not raise an exception
    with patch('sys.argv', ['zrdata', 'rating', '12345']):
      result = main()
      assert result is None

  def test_cli_handles_result_command(self):
    """Test that CLI accepts result command."""
    with patch('sys.argv', ['zrdata', 'result', '3590800']):
      result = main()
      assert result is None

  def test_cli_handles_team_command(self):
    """Test that CLI accepts team command."""
    with patch('sys.argv', ['zrdata', 'team', '456']):
      result = main()
      assert result is None

  def test_cli_accepts_short_options(self):
    """Test that CLI accepts short option flags."""
    with patch('sys.argv', ['zrdata', '-v', '-r', 'rating', '123']):
      result = main()
      assert result is None

  def test_cli_accepts_long_options(self):
    """Test that CLI accepts long option flags."""
    with patch('sys.argv', ['zrdata', '--verbose', '--raw', 'rating', '123']):
      result = main()
      assert result is None


# ===============================================================================
class TestCLIEntryPoint:
  """Test CLI as entry point."""

  def test_main_function_returns_none_on_success(self):
    """Test that main returns None (which becomes exit code 0)."""
    with patch('sys.argv', ['zrdata']):
      result = main()
      assert result is None

  def test_main_can_be_called_as_entry_point(self):
    """Test that main function has correct signature for entry point."""
    # Main should accept no arguments and return int | None
    with patch('sys.argv', ['zrdata']):
      result = main()
      assert result is None or isinstance(result, int)
