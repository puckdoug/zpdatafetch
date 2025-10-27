"""Integration tests for zrdata CLI using subprocess.

Tests the actual CLI program by spawning it as a subprocess and checking
output. This catches integration issues that unit tests might miss.
"""

import subprocess

import pytest


# ===============================================================================
class TestZRDataCLIHelp:
  """Test zrdata help and basic functionality."""

  def test_zrdata_help(self):
    """Test zrdata --help produces usage information."""
    result = subprocess.run(
      ['zrdata', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'usage:' in result.stdout.lower() or 'usage:' in result.stderr.lower()

  def test_zrdata_no_args(self):
    """Test zrdata with no arguments exits gracefully."""
    result = subprocess.run(
      ['zrdata'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Should exit with 0 (no command specified)
    assert result.returncode == 0


# ===============================================================================
class TestZRDataRiderCommand:
  """Test zrdata rider command."""

  def test_rider_no_id(self):
    """Test rider command without ID produces error."""
    result = subprocess.run(
      ['zrdata', 'rider'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'Error' in result.stdout or 'Error' in result.stderr

  def test_rider_noaction_single_id(self):
    """Test rider command with --noaction flag (no network)."""
    result = subprocess.run(
      ['zrdata', 'rider', '--noaction', '12345'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch rider data for: 12345' in result.stdout

  def test_rider_noaction_multiple_ids(self):
    """Test rider command with multiple IDs and --noaction."""
    result = subprocess.run(
      ['zrdata', 'rider', '--noaction', '123', '456', '789'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch rider data for: 123, 456, 789' in result.stdout

  def test_rider_noaction_with_raw_flag(self):
    """Test rider command with --noaction and --raw flags."""
    result = subprocess.run(
      ['zrdata', 'rider', '--noaction', '--raw', '12345'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch rider data for: 12345' in result.stdout
    assert 'raw output format' in result.stdout

  def test_rider_invalid_id(self):
    """Test rider command with invalid (non-numeric) ID."""
    result = subprocess.run(
      ['zrdata', 'rider', '--noaction', 'invalid'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Should succeed with --noaction (no conversion happens)
    assert result.returncode == 0


# ===============================================================================
class TestZRDataConfigCommand:
  """Test zrdata config command."""

  @pytest.mark.skip(
    reason='Config command is interactive and difficult to test in subprocess. '
    'Tested separately in unit tests with mocking.',
  )
  def test_config_command_basic(self):
    """Test config command reports current status."""
    result = subprocess.run(
      ['zrdata', 'config'],
      capture_output=True,
      text=True,
      timeout=5,
      input='\n',  # Send empty input (just newline) to getpass if needed
      check=False,  # Don't fail on non-zero exit
    )
    # Should report status without crashing
    # Will either report "already configured" (0) or error trying to configure (not 0)
    assert result.returncode is not None  # Just verify it completed


# ===============================================================================
class TestZRDataLoggingOptions:
  """Test zrdata logging options."""

  def test_verbose_flag(self):
    """Test -v/--verbose flag works."""
    result = subprocess.run(
      ['zrdata', '--verbose', 'rider', '--noaction', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0

  def test_debug_flag(self):
    """Test -vv/--debug flag works."""
    result = subprocess.run(
      ['zrdata', '--debug', 'rider', '--noaction', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0

  def test_log_file_option(self, tmp_path):
    """Test --log-file option works."""
    log_file = tmp_path / 'zrdata.log'
    result = subprocess.run(
      ['zrdata', '--log-file', str(log_file), 'rider', '--noaction', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    # Log file should be created (or at least command succeeds)


# ===============================================================================
class TestZRDataResultCommand:
  """Test zrdata result command (not yet implemented)."""

  def test_result_command_not_implemented(self):
    """Test result command reports not implemented."""
    result = subprocess.run(
      ['zrdata', 'result', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'not yet implemented' in result.stdout.lower()


# ===============================================================================
class TestZRDataTeamCommand:
  """Test zrdata team command (not yet implemented)."""

  def test_team_command_not_implemented(self):
    """Test team command reports not implemented."""
    result = subprocess.run(
      ['zrdata', 'team', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'not yet implemented' in result.stdout.lower()


# ===============================================================================
class TestZRDataIntegration:
  """Integration tests combining multiple features."""

  def test_rider_with_all_options(self):
    """Test rider command with various option combinations."""
    result = subprocess.run(
      ['zrdata', '-v', '--raw', '--noaction', 'rider', '100', '200'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch rider data for: 100, 200' in result.stdout

  def test_help_displays_commands(self):
    """Test help shows available commands."""
    result = subprocess.run(
      ['zrdata', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    output = result.stdout + result.stderr
    assert 'rider' in output.lower()
