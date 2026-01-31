"""Integration tests for zdata CLI using subprocess.

Tests the actual CLI program by spawning it as a subprocess and checking
output. This catches integration issues that unit tests might miss.
"""

import subprocess


class TestZDataCLIHelp:
  """Test zdata help and basic functionality."""

  def test_zdata_help(self):
    """Test zdata --help produces usage information."""
    result = subprocess.run(
      ['zdata', '--help'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'usage:' in result.stdout.lower() or 'usage:' in result.stderr.lower()

  def test_zdata_no_args(self):
    """Test zdata with no arguments exits gracefully."""
    result = subprocess.run(
      ['zdata'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    # Should exit with 0 (no command specified)
    assert result.returncode == 0

  def test_zdata_version(self):
    """Test zdata --version outputs version information."""
    result = subprocess.run(
      ['zdata', '--version'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    # Version output goes to stdout
    output = result.stdout + result.stderr
    # Should contain "zdata" and a version number (e.g., "2.0.2")
    assert 'zdata' in output.lower()
    # Check for version pattern (digits.digits.digits or "unknown")
    assert any(char.isdigit() for char in output) or 'unknown' in output.lower()


class TestZDataProfileCommand:
  """Test zdata profile command."""

  def test_profile_no_id(self):
    """Test profile command without ID produces error."""
    result = subprocess.run(
      ['zdata', 'profile'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 1
    assert 'Error' in result.stdout or 'Error' in result.stderr

  def test_profile_noaction_single_id(self):
    """Test profile command with --noaction flag (no network)."""
    result = subprocess.run(
      ['zdata', 'profile', '--noaction', '550564'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch profile data for: 550564' in result.stdout

  def test_profile_noaction_multiple_ids(self):
    """Test profile command with multiple IDs and --noaction."""
    result = subprocess.run(
      ['zdata', 'profile', '--noaction', '550564', '123456'],
      capture_output=True,
      text=True,
      timeout=5,
      check=False,
    )
    assert result.returncode == 0
    assert 'Would fetch profile data for: 550564, 123456' in result.stdout
