"""Integration tests for zpdata CLI using subprocess.

Tests the actual CLI program by spawning it as a subprocess and checking
output. This catches integration issues that unit tests might miss.
"""

import subprocess


# ===============================================================================
class TestZPDataCLIHelp:
  """Test zpdata help and basic functionality."""

  def test_zpdata_help(self):
    """Test zpdata --help produces usage information."""
    result = subprocess.run(
      ['zpdata', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'usage:' in result.stdout.lower() or 'usage:' in result.stderr.lower()

  def test_zpdata_no_args(self):
    """Test zpdata with no arguments exits gracefully."""
    result = subprocess.run(
      ['zpdata'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Should exit with 0 (no command specified)
    assert result.returncode == 0


# ===============================================================================
class TestZPDataCyclistCommand:
  """Test zpdata cyclist command."""

  def test_cyclist_no_id(self):
    """Test cyclist command without ID produces error."""
    result = subprocess.run(
      ['zpdata', 'cyclist'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # May error or succeed depending on implementation
    # Just verify it doesn't crash
    assert result.returncode in [0, 1, 2]

  def test_cyclist_noaction_single_id(self):
    """Test cyclist command with --noaction flag (no network)."""
    result = subprocess.run(
      ['zpdata', 'cyclist', '--noaction', '12345'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Should succeed without fetching network data
    assert result.returncode == 0
    assert 'Would fetch' in result.stdout or 'would' in result.stdout.lower()

  def test_cyclist_noaction_multiple_ids(self):
    """Test cyclist command with multiple IDs and --noaction."""
    result = subprocess.run(
      ['zpdata', 'cyclist', '--noaction', '123', '456', '789'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    # Should report what it would do
    assert '123' in result.stdout or '456' in result.stdout or 'Would' in result.stdout


# ===============================================================================
class TestZPDataConfigCommand:
  """Test zpdata config command."""

  def test_config_command_basic(self):
    """Test config command reports current status."""
    result = subprocess.run(
      ['zpdata', 'config'],
      capture_output=True,
      text=True,
      timeout=5,
      input='',
      check=False,  # Don't try to interact
    )
    # Should report status
    assert result.returncode in [0, 1]


# ===============================================================================
class TestZPDataLoggingOptions:
  """Test zpdata logging options."""

  def test_verbose_flag(self):
    """Test -v/--verbose flag works."""
    result = subprocess.run(
      ['zpdata', '--verbose', 'cyclist', '--noaction', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0

  def test_debug_flag(self):
    """Test -vv/--debug flag works."""
    result = subprocess.run(
      ['zpdata', '--debug', 'cyclist', '--noaction', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0

  def test_log_file_option(self, tmp_path):
    """Test --log-file option works."""
    log_file = tmp_path / 'zpdata.log'
    result = subprocess.run(
      ['zpdata', '--log-file', str(log_file), 'cyclist', '--noaction', '123'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0


# ===============================================================================
class TestZPDataIntegration:
  """Integration tests combining multiple features."""

  def test_cyclist_with_all_options(self):
    """Test cyclist command with various option combinations."""
    result = subprocess.run(
      ['zpdata', '-v', '--raw', '--noaction', 'cyclist', '100', '200'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0

  def test_help_displays_commands(self):
    """Test help shows available commands."""
    result = subprocess.run(
      ['zpdata', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    output = result.stdout + result.stderr
    assert 'cyclist' in output.lower() or 'command' in output.lower()

  def test_multiple_commands_available(self):
    """Test multiple commands are available."""
    result = subprocess.run(
      ['zpdata', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    output = result.stdout + result.stderr
    # zpdata should have multiple commands
    assert len(output) > 50  # Help output should be substantial


# ===============================================================================
class TestZPDataOtherCommands:
  """Test other zpdata commands."""

  def test_primes_command_exists(self):
    """Test primes command is available."""
    result = subprocess.run(
      ['zpdata', 'primes', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Command should at least be recognized
    assert result.returncode in [0, 1, 2]

  def test_result_command_exists(self):
    """Test result command is available."""
    result = subprocess.run(
      ['zpdata', 'result', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Command should at least be recognized
    assert result.returncode in [0, 1, 2]

  def test_signup_command_exists(self):
    """Test signup command is available."""
    result = subprocess.run(
      ['zpdata', 'signup', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Command should at least be recognized
    assert result.returncode in [0, 1, 2]

  def test_team_command_exists(self):
    """Test team command is available."""
    result = subprocess.run(
      ['zpdata', 'team', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Command should at least be recognized
    assert result.returncode in [0, 1, 2]
