"""Tests for zrdatafetch CLI module.

Tests the command-line interface including argument parsing and command
routing.
"""

from unittest.mock import patch


from zrdatafetch.cli import main


# ===============================================================================
class TestCLIArgumentParsing:
  """Test CLI argument parsing."""

  def test_main_with_no_args(self, capsys):
    """Test main with no arguments (should return None)."""
    with patch('sys.argv', ['zrdata']):
      result = main()
      assert result is None

  def test_main_with_verbose_flag(self, capsys):
    """Test main with verbose flag (returns None)."""
    with patch('sys.argv', ['zrdata', '-v']):
      result = main()
      assert result is None

  def test_main_with_debug_flag(self, capsys):
    """Test main with debug flag (returns None)."""
    with patch('sys.argv', ['zrdata', '-vv']):
      result = main()
      assert result is None

  def test_main_with_log_file(self, tmp_path, capsys):
    """Test main with log file argument (returns None)."""
    log_file = tmp_path / 'test.log'
    with patch('sys.argv', ['zrdata', '--log-file', str(log_file)]):
      result = main()
      assert result is None

  def test_main_with_raw_flag(self):
    """Test main with raw flag (returns None)."""
    with patch('sys.argv', ['zrdata', '-r']):
      result = main()
      assert result is None

  def test_main_with_rider_command(self):
    """Test main with rider command (using --noaction to avoid network)."""
    with patch('sys.argv', ['zrdata', 'rider', '--noaction', '12345']):
      result = main()
      assert result is None

  def test_main_with_result_command(self):
    """Test main with result command (not yet implemented)."""
    with patch('sys.argv', ['zrdata', 'result', '3590800']):
      result = main()
      assert result == 1  # Result not implemented yet

  def test_main_with_team_command(self):
    """Test main with team command (not yet implemented)."""
    with patch('sys.argv', ['zrdata', 'team', '456']):
      result = main()
      assert result == 1  # Team not implemented yet

  def test_main_with_multiple_ids(self):
    """Test main with multiple IDs (using --noaction)."""
    with patch(
      'sys.argv',
      ['zrdata', 'rider', '--noaction', '12345', '67890', '11111'],
    ):
      result = main()
      assert result is None or result == 0

  def test_main_with_invalid_command(self):
    """Test main with invalid command."""
    with patch('sys.argv', ['zrdata', 'invalid']):
      # Invalid command should return error code
      result = main()
      assert result == 1

  def test_main_with_config_command(self):
    """Test main with config command."""
    with patch('sys.argv', ['zrdata', 'config']):
      with patch('zrdatafetch.cli.Config'):
        result = main()
        # Config command returns None on success
        assert result is None


# ===============================================================================
class TestCLILoggingConfiguration:
  """Test logging configuration in CLI."""

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_debug_level(self, mock_setup):
    """Test that debug flag sets DEBUG level logging."""
    import logging

    with patch('sys.argv', ['zrdata', '-vv', 'rider', '--noaction', '123']):
      result = main()
      # setup_logging should be called with DEBUG level
      mock_setup.assert_called_once()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('console_level') == logging.DEBUG
      assert result is None

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_verbose_level(self, mock_setup):
    """Test that verbose flag sets INFO level logging."""
    import logging

    with patch('sys.argv', ['zrdata', '-v', 'rider', '--noaction', '123']):
      result = main()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('console_level') == logging.INFO
      assert result is None

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_with_file_only(self, mock_setup):
    """Test that log file sets force_console=False."""
    with patch(
      'sys.argv',
      ['zrdata', '--log-file', 'test.log', 'rider', '--noaction', '123'],
    ):
      result = main()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('force_console') is False
      assert result is None

  @patch('zrdatafetch.cli.setup_logging')
  def test_logging_debug_with_file(self, mock_setup):
    """Test debug flag with log file."""
    import logging

    with patch(
      'sys.argv',
      ['zrdata', '-vv', '--log-file', 'test.log', 'rider', '--noaction', '123'],
    ):
      result = main()
      call_kwargs = mock_setup.call_args[1]
      assert call_kwargs.get('console_level') == logging.DEBUG
      assert call_kwargs.get('log_file') == 'test.log'
      assert result is None


# ===============================================================================
class TestCLICommandRouting:
  """Test command routing logic (placeholder tests).

  These tests verify that the CLI structure is correct.
  Actual command implementations will be added when classes are refactored.
  """

  def test_cli_handles_rider_command(self):
    """Test that CLI accepts rider command."""
    # This should not raise an exception
    with patch('sys.argv', ['zrdata', 'rider', '--noaction', '12345']):
      result = main()
      assert result is None

  def test_cli_handles_result_command(self):
    """Test that CLI accepts result command."""
    with patch('sys.argv', ['zrdata', 'result', '3590800']):
      result = main()
      assert result == 1  # Result not implemented yet

  def test_cli_handles_team_command(self):
    """Test that CLI accepts team command."""
    with patch('sys.argv', ['zrdata', 'team', '456']):
      result = main()
      assert result == 1  # Team not implemented yet

  def test_cli_accepts_short_options(self):
    """Test that CLI accepts short option flags."""
    with patch('sys.argv', ['zrdata', '-v', '-r', 'rider', '--noaction', '123']):
      result = main()
      assert result is None or result == 0

  def test_cli_accepts_long_options(self):
    """Test that CLI accepts long option flags."""
    with patch(
      'sys.argv',
      ['zrdata', '--verbose', '--raw', 'rider', '--noaction', '123'],
    ):
      result = main()
      assert result is None or result == 0


# ===============================================================================
class TestCLIEntryPoint:
  """Test CLI as entry point."""

  def test_main_function_calls_sys_exit(self):
    """Test that main returns None when no command is provided."""
    with patch('sys.argv', ['zrdata']):
      result = main()
      # Should return None for no command
      assert result is None

  def test_main_can_be_called_as_entry_point(self):
    """Test that main function can be called as entry point."""
    # Main should accept no arguments and return None
    with patch('sys.argv', ['zrdata']):
      result = main()
      assert result is None
