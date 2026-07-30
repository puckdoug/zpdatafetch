"""Tests for zsdatafetch CLI."""

import json
import logging
from unittest.mock import patch

import httpx2

from zsdatafetch.cli import main
from zsdatafetch.zs import ZS_obj
from zsdatafetch.zsincidentfetch import ZSIncidentFetch
from zsdatafetch.zsmaintenancefetch import ZSMaintenanceFetch
from zsdatafetch.zssummaryfetch import ZSSummaryFetch


class TestCLI:
  """Tests for zsdata CLI commands."""

  def setup_method(self):
    ZS_obj.close_client()
    ZSSummaryFetch.set_sync_mode(True)
    ZSIncidentFetch.set_sync_mode(True)
    ZSMaintenanceFetch.set_sync_mode(True)

  def teardown_method(self):
    ZS_obj.close_client()
    ZSSummaryFetch.set_sync_mode(False)
    ZSIncidentFetch.set_sync_mode(False)
    ZSMaintenanceFetch.set_sync_mode(False)

  def test_no_command(self, capsys):
    with patch('sys.argv', ['zsdata']):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'usage' in captured.out.lower() or 'module' in captured.out.lower()

  def test_invalid_command(self, capsys):
    with patch('sys.argv', ['zsdata', 'bogus']):
      result = main()
    assert result == 1
    captured = capsys.readouterr()
    assert 'Unknown command' in captured.err

  def test_help_command(self, capsys):
    with patch('sys.argv', ['zsdata', 'help']):
      result = main()
    assert result is None

  # -- noaction tests --

  def test_status_noaction(self, capsys):
    with patch('sys.argv', ['zsdata', 'status', '--noaction']):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'Would fetch status summary' in captured.out

  def test_status_components_noaction(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', 'status', '--components', '--noaction'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'components' in captured.out

  def test_incidents_noaction(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', 'incidents', '--noaction'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'Would fetch all incidents' in captured.out

  def test_incidents_unresolved_noaction(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', 'incidents', '--unresolved', '--noaction'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'unresolved' in captured.out

  def test_maintenance_noaction(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', 'maintenance', '--noaction'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'Would fetch all maintenance' in captured.out

  def test_maintenance_upcoming_noaction(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', 'maintenance', '--upcoming', '--noaction'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'upcoming' in captured.out

  def test_maintenance_active_noaction(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', 'maintenance', '--active', '--noaction'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'active' in captured.out

  # -- fetch tests with mock transport --

  def test_status_command(self, summary_json, capsys):
    def handler(request):
      return httpx2.Response(
        200,
        text=summary_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    with patch('sys.argv', ['zsdata', 'status', '--sync']):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    assert 'Status:' in captured.out

  def test_status_raw(self, summary_json, capsys):
    def handler(request):
      return httpx2.Response(
        200,
        text=summary_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    with patch(
      'sys.argv',
      ['zsdata', 'status', '--raw', '--sync'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert 'page' in parsed

  def test_status_json(self, summary_json, capsys):
    def handler(request):
      return httpx2.Response(
        200,
        text=summary_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    with patch(
      'sys.argv',
      ['zsdata', 'status', '--json', '--sync'],
    ):
      result = main()
    assert result is None
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert 'page' in parsed

  def test_incidents_command(self, incidents_json, capsys):
    def handler(request):
      return httpx2.Response(
        200,
        text=incidents_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    with patch(
      'sys.argv',
      ['zsdata', 'incidents', '--sync'],
    ):
      result = main()
    assert result is None

  def test_maintenance_command(
    self,
    maintenance_json,
    capsys,
  ):
    def handler(request):
      return httpx2.Response(
        200,
        text=maintenance_json,
        request=request,
      )

    ZS_obj._client = httpx2.Client(
      transport=httpx2.MockTransport(handler),
    )
    with patch(
      'sys.argv',
      ['zsdata', 'maintenance', '--sync'],
    ):
      result = main()
    assert result is None

  # -- logging tests --

  def test_verbose_logging(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', '-v', 'status', '--noaction'],
    ):
      with patch(
        'zsdatafetch.cli.setup_logging',
      ) as mock_setup:
        result = main()
    assert result is None
    mock_setup.assert_called_once()
    call_kwargs = mock_setup.call_args[1]
    assert call_kwargs.get('console_level') == logging.INFO

  def test_debug_logging(self, capsys):
    with patch(
      'sys.argv',
      ['zsdata', '-vv', 'status', '--noaction'],
    ):
      with patch(
        'zsdatafetch.cli.setup_logging',
      ) as mock_setup:
        result = main()
    assert result is None
    mock_setup.assert_called_once()
    call_kwargs = mock_setup.call_args[1]
    assert call_kwargs.get('console_level') == logging.DEBUG
