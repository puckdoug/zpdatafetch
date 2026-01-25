"""Tests for CLI profile command output."""

import sys

import httpx

from zdatafetch.cli import main


def test_cli_single_profile_output(combined_handler, monkeypatch, capsys):
  """Test CLI output for single profile shows all data."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = 'test@example.com'
    password = 'testpassword'

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, 'Config', MockConfig)
  monkeypatch.setattr('zdatafetch.cli.Config', MockConfig)

  # Mock sys.argv for single profile
  monkeypatch.setattr(sys, 'argv', ['zdata', 'profile', '550564'])

  try:
    # Run CLI
    result = main()
    assert result is None

    # Check output
    captured = capsys.readouterr()
    output = captured.out

    # Verify it's ZwiftProfile output format
    assert 'ZwiftProfile(' in output
    assert 'id: 550564' in output
    assert 'firstName:' in output
    assert 'lastName:' in output
    assert 'ftp:' in output

    # Verify it shows multiple fields (not just 3)
    assert 'male:' in output
    assert 'countryAlpha3:' in output

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_cli_multiple_profiles_output(combined_handler, monkeypatch, capsys):
  """Test CLI output for multiple profiles shows dictionary format with IDs."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = 'test@example.com'
    password = 'testpassword'

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, 'Config', MockConfig)
  monkeypatch.setattr('zdatafetch.cli.Config', MockConfig)

  # Mock sys.argv for multiple profiles
  monkeypatch.setattr(sys, 'argv', ['zdata', 'profile', '550564', '123456'])

  try:
    # Run CLI
    result = main()
    assert result is None

    # Check output
    captured = capsys.readouterr()
    output = captured.out

    # Verify it's dictionary format
    assert output.startswith('{')
    assert output.rstrip().endswith('}')

    # Verify both IDs are present as keys
    assert '550564:' in output
    assert '123456:' in output

    # Verify each entry is a ZwiftProfile
    assert 'ZwiftProfile(' in output

    # Count how many ZwiftProfile entries (should be 2)
    assert output.count('ZwiftProfile(') == 2

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_cli_single_profile_raw_output(combined_handler, monkeypatch, capsys):
  """Test CLI raw output for single profile."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = 'test@example.com'
    password = 'testpassword'

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, 'Config', MockConfig)
  monkeypatch.setattr('zdatafetch.cli.Config', MockConfig)

  # Mock sys.argv for single profile with --raw
  monkeypatch.setattr(sys, 'argv', ['zdata', 'profile', '--raw', '550564'])

  try:
    # Run CLI
    result = main()
    assert result is None

    # Check output
    captured = capsys.readouterr()
    output = captured.out

    # Verify it's raw JSON (not ZwiftProfile format)
    assert 'ZwiftProfile(' not in output
    assert '"id": 550564' in output or '"id":550564' in output
    assert '"firstName"' in output

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_cli_multiple_profiles_raw_output(
  combined_handler, monkeypatch, capsys
):
  """Test CLI raw output for multiple profiles."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = 'test@example.com'
    password = 'testpassword'

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, 'Config', MockConfig)
  monkeypatch.setattr('zdatafetch.cli.Config', MockConfig)

  # Mock sys.argv for multiple profiles with --raw
  monkeypatch.setattr(
    sys, 'argv', ['zdata', 'profile', '--raw', '550564', '123456']
  )

  try:
    # Run CLI
    result = main()
    assert result is None

    # Check output
    captured = capsys.readouterr()
    output = captured.out

    # Verify it shows ID: raw_json format
    assert '550564:' in output
    assert '123456:' in output
    assert '"firstName"' in output

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_cli_profile_missing_credentials(monkeypatch, capsys):
  """Test CLI handles missing credentials gracefully."""
  import zdatafetch.profile

  # Mock the config to return empty credentials
  class MockConfig:
    username = ''
    password = ''

    def load(self):
      pass

  monkeypatch.setattr(zdatafetch.profile, 'Config', MockConfig)

  # Mock sys.argv
  monkeypatch.setattr(sys, 'argv', ['zdata', 'profile', '550564'])

  # Run CLI - should return error code
  result = main()

  # Check it returned error
  assert result == 1

  # Check error message
  captured = capsys.readouterr()
  assert (
    'credentials not found' in captured.err.lower()
    or 'credentials not found' in captured.out.lower()
  )
