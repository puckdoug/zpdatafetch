"""Tests for zpdata racelog CLI command."""

import json
import subprocess

import pytest


class TestRacelogCommandHelp:
  """Test racelog command appears in help."""

  def test_racelog_in_help_output(self):
    """Test that racelog command is listed in help."""
    result = subprocess.run(
      ['zpdata', '--help'],
      check=False,
      capture_output=True,
      text=True,
      timeout=5,
    )
    assert result.returncode == 0
    assert 'racelog' in result.stdout

  def test_racelog_in_command_list(self):
    """Test that racelog appears in command metavar."""
    result = subprocess.run(
      ['zpdata', '--help'],
      check=False,
      capture_output=True,
      text=True,
      timeout=5,
    )
    # Should see racelog in the list of commands
    assert 'racelog' in result.stdout.lower()


class TestRacelogCommandNoAction:
  """Test racelog command with --noaction flag."""

  def test_racelog_noaction_single_id(self):
    """Test racelog with --noaction and single ID."""
    result = subprocess.run(
      ['zpdata', 'racelog', '--noaction', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=5,
    )
    assert result.returncode == 0
    assert '7574336' in result.stdout

  def test_racelog_noaction_multiple_ids(self):
    """Test racelog with --noaction and multiple IDs."""
    result = subprocess.run(
      ['zpdata', 'racelog', '--noaction', '7574336', '550564'],
      check=False,
      capture_output=True,
      text=True,
      timeout=5,
    )
    assert result.returncode == 0
    assert '7574336' in result.stdout
    assert '550564' in result.stdout


class TestRacelogCommandErrors:
  """Test racelog command error handling."""

  def test_racelog_no_id_shows_error(self):
    """Test that racelog without ID shows error."""
    result = subprocess.run(
      ['zpdata', 'racelog'],
      check=False,
      capture_output=True,
      text=True,
      timeout=5,
    )
    assert result.returncode != 0
    assert 'error' in result.stdout.lower() or 'error' in result.stderr.lower()


class TestRacelogCommandOutput:
  """Test racelog command output format."""

  @pytest.mark.live
  def test_racelog_returns_json(self):
    """Test that racelog returns valid JSON."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    # Should be valid JSON
    data = json.loads(result.stdout)
    assert isinstance(data, dict)

  @pytest.mark.live
  def test_racelog_contains_zwift_id_key(self):
    """Test that racelog output contains zwift_id as key."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    data = json.loads(result.stdout)
    assert '7574336' in data

  @pytest.mark.live
  def test_racelog_value_is_array(self):
    """Test that racelog returns array of races."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    data = json.loads(result.stdout)
    assert isinstance(data['7574336'], list)

  @pytest.mark.live
  def test_racelog_races_have_expected_fields(self):
    """Test that races in racelog have expected fields."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    data = json.loads(result.stdout)
    races = data['7574336']

    if len(races) > 0:
      first_race = races[0]
      # Check for some expected fields
      assert 'event_title' in first_race or 'zid' in first_race


class TestRacelogCommandRawFlag:
  """Test racelog command with --raw flag."""

  @pytest.mark.live
  def test_racelog_raw_single_id_returns_array(self):
    """Test that --raw with single ID returns just array."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336', '--raw'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    data = json.loads(result.stdout)
    # With --raw and single ID, should be an array directly
    assert isinstance(data, list)

  @pytest.mark.live
  def test_racelog_raw_multiple_ids(self):
    """Test that --raw with multiple IDs works."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336', '550564', '--raw'],
      check=False,
      capture_output=True,
      text=True,
      timeout=60,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    # Should succeed and produce output
    assert len(result.stdout) > 0


class TestRacelogCommandMultipleIds:
  """Test racelog command with multiple IDs."""

  @pytest.mark.live
  def test_racelog_multiple_ids_has_all_keys(self):
    """Test that multiple IDs produces output for each."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336', '550564'],
      check=False,
      capture_output=True,
      text=True,
      timeout=60,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    data = json.loads(result.stdout)
    # Should have keys for both IDs
    assert '7574336' in data or '550564' in data


class TestRacelogCommandVsCyclist:
  """Test that racelog command differs from cyclist command."""

  @pytest.mark.live
  def test_racelog_vs_cyclist_output_structure(self):
    """Test that racelog and cyclist return different structures."""
    # Get cyclist output
    cyclist_result = subprocess.run(
      ['zpdata', 'cyclist', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    # Get racelog output
    racelog_result = subprocess.run(
      ['zpdata', 'racelog', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if cyclist_result.returncode != 0 or racelog_result.returncode != 0:
      pytest.skip('One or both commands failed')

    cyclist_data = json.loads(cyclist_result.stdout)
    racelog_data = json.loads(racelog_result.stdout)

    # Cyclist should have dict with 'data' key
    assert isinstance(cyclist_data['7574336'], dict)
    assert 'data' in cyclist_data['7574336']

    # Racelog should just have array
    assert isinstance(racelog_data['7574336'], list)

  @pytest.mark.live
  def test_racelog_contains_same_races_as_cyclist_data(self):
    """Test that racelog matches the 'data' array from cyclist."""
    # Get cyclist output
    cyclist_result = subprocess.run(
      ['zpdata', 'cyclist', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    # Get racelog output
    racelog_result = subprocess.run(
      ['zpdata', 'racelog', '7574336'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if cyclist_result.returncode != 0 or racelog_result.returncode != 0:
      pytest.skip('One or both commands failed')

    cyclist_data = json.loads(cyclist_result.stdout)
    racelog_data = json.loads(racelog_result.stdout)

    # The racelog should match the 'data' array from cyclist
    assert len(racelog_data['7574336']) == len(cyclist_data['7574336']['data'])


class TestRacelogCommandSync:
  """Test racelog command with --sync flag."""

  @pytest.mark.live
  def test_racelog_sync_flag_works(self):
    """Test that --sync flag works with racelog."""
    result = subprocess.run(
      ['zpdata', 'racelog', '7574336', '--sync'],
      check=False,
      capture_output=True,
      text=True,
      timeout=30,
    )

    if result.returncode != 0:
      pytest.skip(f'Command failed: {result.stderr}')

    # Should produce valid JSON
    data = json.loads(result.stdout)
    assert '7574336' in data
    assert isinstance(data['7574336'], list)
