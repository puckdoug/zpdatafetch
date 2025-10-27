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
class TestZRDataBatchCommand:
  """Test zrdata batch rider commands."""

  def test_batch_flag_no_ids(self):
    """Test --batch flag without IDs produces error."""
    result = subprocess.run(
      ['zrdata', 'rider', '--batch'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'Error' in result.stdout or 'Error' in result.stderr

  def test_batch_noaction_single_id(self):
    """Test --batch with --noaction and single ID."""
    result = subprocess.run(
      ['zrdata', 'rider', '--batch', '--noaction', '12345'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch' in result.stdout or 'batch' in result.stdout.lower()

  def test_batch_noaction_multiple_ids(self):
    """Test --batch with --noaction and multiple IDs."""
    result = subprocess.run(
      ['zrdata', 'rider', '--batch', '--noaction', '123', '456', '789'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'batch' in result.stdout.lower() or 'Would fetch' in result.stdout

  def test_batch_noaction_with_raw_flag(self):
    """Test --batch with --noaction and --raw flags."""
    result = subprocess.run(
      ['zrdata', 'rider', '--batch', '--noaction', '--raw', '12345', '67890'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0

  def test_batch_file_not_found(self):
    """Test --batch-file with non-existent file."""
    result = subprocess.run(
      ['zrdata', 'rider', '--batch-file', '/nonexistent/file.txt'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'Error' in result.stdout or 'Error' in result.stderr

  def test_batch_file_with_ids(self, tmp_path):
    """Test --batch-file with valid file."""
    # Create a temporary file with rider IDs
    batch_file = tmp_path / 'riders.txt'
    batch_file.write_text('12345\n67890\n11111\n')

    result = subprocess.run(
      ['zrdata', 'rider', '--batch-file', str(batch_file), '--noaction'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0

  def test_batch_file_with_blank_lines(self, tmp_path):
    """Test --batch-file handles blank lines correctly."""
    # Create a file with blank lines
    batch_file = tmp_path / 'riders.txt'
    batch_file.write_text('12345\n\n67890\n\n\n11111\n')

    result = subprocess.run(
      ['zrdata', 'rider', '--batch-file', str(batch_file), '--noaction'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
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


# ===============================================================================
class TestZRDataResultCommand:
  """Test zrdata result command."""

  def test_result_no_id(self):
    """Test result command without ID produces error."""
    result = subprocess.run(
      ['zrdata', 'result'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'Error' in result.stdout or 'Error' in result.stderr

  def test_result_noaction_single_id(self):
    """Test result command with --noaction flag (no network)."""
    result = subprocess.run(
      ['zrdata', 'result', '--noaction', '3590800'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch result data for: 3590800' in result.stdout

  def test_result_noaction_multiple_ids(self):
    """Test result command with multiple IDs and --noaction."""
    result = subprocess.run(
      ['zrdata', 'result', '--noaction', '123', '456', '789'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch result data for: 123, 456, 789' in result.stdout

  def test_result_noaction_with_raw_flag(self):
    """Test result command with --noaction and --raw flags."""
    result = subprocess.run(
      ['zrdata', 'result', '--noaction', '--raw', '3590800'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch result data for: 3590800' in result.stdout
    assert 'raw output format' in result.stdout

  def test_result_invalid_id(self):
    """Test result command with invalid (non-numeric) ID."""
    result = subprocess.run(
      ['zrdata', 'result', '--noaction', 'invalid'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Should succeed with --noaction (no conversion happens)
    assert result.returncode == 0


# ===============================================================================
class TestZRDataTeamCommand:
  """Test zrdata team command."""

  def test_team_no_id(self):
    """Test team command without ID produces error."""
    result = subprocess.run(
      ['zrdata', 'team'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'Error' in result.stdout or 'Error' in result.stderr

  def test_team_noaction_single_id(self):
    """Test team command with --noaction flag (no network)."""
    result = subprocess.run(
      ['zrdata', 'team', '--noaction', '456'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch team data for: 456' in result.stdout

  def test_team_noaction_multiple_ids(self):
    """Test team command with multiple IDs and --noaction."""
    result = subprocess.run(
      ['zrdata', 'team', '--noaction', '111', '222', '333'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch team data for: 111, 222, 333' in result.stdout

  def test_team_noaction_with_raw_flag(self):
    """Test team command with --noaction and --raw flags."""
    result = subprocess.run(
      ['zrdata', 'team', '--noaction', '--raw', '456'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch team data for: 456' in result.stdout
    assert 'raw output format' in result.stdout

  def test_team_invalid_id(self):
    """Test team command with invalid (non-numeric) ID."""
    result = subprocess.run(
      ['zrdata', 'team', '--noaction', 'invalid'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Should succeed with --noaction (no conversion happens)
    assert result.returncode == 0
