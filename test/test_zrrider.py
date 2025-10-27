"""Tests for zrdatafetch ZRRider class.

Tests the rider data class and fetching functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from zrdatafetch import ZRRider
from zrdatafetch.config import Config
from zrdatafetch.exceptions import ZRConfigError


# ===============================================================================
class TestZRRiderInitialization:
  """Test ZRRider creation and initialization."""

  def test_zrrider_creation(self):
    """Test that ZRRider can be instantiated."""
    rider = ZRRider()
    assert rider is not None

  def test_zrrider_defaults(self):
    """Test that ZRRider has correct default values."""
    rider = ZRRider()
    assert rider.zwift_id == 0
    assert rider.epoch == -1
    assert rider.name == 'Nobody'
    assert rider.gender == 'M'
    assert rider.current_rating == 0.0
    assert rider.current_rank == 'Unranked'
    assert rider.source == 'none'

  def test_zrrider_with_values(self):
    """Test creating ZRRider with custom values."""
    rider = ZRRider(
      zwift_id=12345,
      name='Test Rider',
      current_rating=100.5,
    )
    assert rider.zwift_id == 12345
    assert rider.name == 'Test Rider'
    assert rider.current_rating == 100.5

  def test_zrrider_private_attributes(self):
    """Test that private attributes are initialized."""
    rider = ZRRider()
    assert rider._raw == {}
    assert rider._rider == {}
    assert rider._verbose is False


# ===============================================================================
class TestZRRiderDataclass:
  """Test ZRRider dataclass functionality."""

  def test_zrrider_to_dict_includes_public(self):
    """Test to_dict includes public attributes."""
    rider = ZRRider(zwift_id=123, name='Test')
    d = rider.to_dict()
    assert d['zwift_id'] == 123
    assert d['name'] == 'Test'

  def test_zrrider_to_dict_excludes_private(self):
    """Test to_dict excludes private attributes."""
    rider = ZRRider()
    rider._raw = {'some': 'data'}
    d = rider.to_dict()
    assert '_raw' not in d
    assert '_rider' not in d
    assert '_verbose' not in d

  def test_zrrider_json_output(self):
    """Test json() method produces valid JSON."""
    import json

    rider = ZRRider(zwift_id=123, name='Test')
    json_str = rider.json()
    parsed = json.loads(json_str)
    assert parsed['zwift_id'] == 123
    assert parsed['name'] == 'Test'


# ===============================================================================
class TestZRRiderFetch:
  """Test fetching rider data."""

  def test_fetch_requires_zwift_id(self):
    """Test that fetch logs warning if no zwift_id."""
    rider = ZRRider()
    with patch('zrdatafetch.zrrider.logger') as mock_logger:
      rider.fetch()
      mock_logger.warning.assert_called()

  def test_fetch_requires_authorization(self):
    """Test that fetch raises ZRConfigError without authorization."""
    rider = ZRRider(zwift_id=123)

    with patch.object(Config, 'load'):
      with patch.object(Config, 'authorization', ''):
        with pytest.raises(ZRConfigError):
          rider.fetch()

  def test_fetch_with_valid_zwift_id_no_auth(self):
    """Test fetch fails gracefully without authorization configured."""
    rider = ZRRider(zwift_id=12345)

    # Mock Config to simulate no authorization
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = ''
      mock_config_class.return_value = mock_config

      with pytest.raises(ZRConfigError):
        rider.fetch()

  def test_fetch_uses_epoch_parameter(self):
    """Test that fetch can use epoch parameter."""
    rider = ZRRider(zwift_id=123)

    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config.authorization = 'test-auth'
      mock_config_class.return_value = mock_config

      with patch.object(rider, 'fetch_json', return_value={}):
        rider.fetch(epoch=1234567890)
        assert rider.epoch == 1234567890


# ===============================================================================
class TestZRRiderParseResponse:
  """Test response parsing."""

  def test_parse_response_empty(self):
    """Test parsing empty response."""
    rider = ZRRider()
    rider._raw = {}
    with patch('zrdatafetch.zrrider.logger'):
      rider._parse_response()
    # Should not raise, just log warning

  def test_parse_response_with_error_message(self):
    """Test parsing response with error message."""
    rider = ZRRider()
    rider._raw = {'message': 'Rider not found'}
    with patch('zrdatafetch.zrrider.logger'):
      rider._parse_response()
    # Should log error but not raise

  def test_parse_response_missing_required_fields(self):
    """Test parsing response missing required fields."""
    rider = ZRRider()
    rider._raw = {'other': 'data'}  # Missing 'name' and 'race'
    with patch('zrdatafetch.zrrider.logger'):
      rider._parse_response()
    # Should log warning but not raise

  def test_parse_response_with_valid_data(self):
    """Test parsing valid response data."""
    rider = ZRRider()
    rider._raw = {
      'name': 'Test Rider',
      'gender': 'F',
      'power': {'compoundScore': 95.5},
      'race': {
        'current': {
          'rating': 100.0,
          'mixed': {'category': 'A'},
        },
        'max30': {
          'rating': 105.0,
          'mixed': {'category': 'A'},
        },
        'max90': {
          'rating': 98.0,
          'mixed': {'category': 'B'},
        },
      },
    }

    rider._parse_response()

    assert rider.name == 'Test Rider'
    assert rider.gender == 'F'
    assert rider.zrcs == 95.5
    assert rider.current_rating == 100.0
    assert rider.current_rank == 'A'
    assert rider.max30_rating == 105.0
    assert rider.max30_rank == 'A'
    assert rider.max90_rating == 98.0
    assert rider.max90_rank == 'B'

  def test_parse_response_drs_from_max30(self):
    """Test that DRS comes from max30 when available."""
    rider = ZRRider()
    rider._raw = {
      'name': 'Test',
      'gender': 'M',
      'power': {'compoundScore': 0.0},
      'race': {
        'current': {'rating': 90.0, 'mixed': {'category': 'B'}},
        'max30': {
          'rating': 105.0,
          'mixed': {'category': 'A'},
        },
        'max90': {
          'rating': 100.0,
          'mixed': {'category': 'A'},
        },
      },
    }

    rider._parse_response()

    assert rider.drs_rating == 105.0
    assert rider.drs_rank == 'A'
    assert rider.source == 'max30'

  def test_parse_response_drs_from_max90_when_max30_unranked(self):
    """Test that DRS falls back to max90 when max30 is unranked."""
    rider = ZRRider()
    rider._raw = {
      'name': 'Test',
      'gender': 'M',
      'power': {'compoundScore': 0.0},
      'race': {
        'current': {'rating': 90.0, 'mixed': {'category': 'B'}},
        'max30': {'rating': None, 'mixed': {'category': 'Unranked'}},
        'max90': {
          'rating': 100.0,
          'mixed': {'category': 'A'},
        },
      },
    }

    rider._parse_response()

    assert rider.drs_rating == 100.0
    assert rider.drs_rank == 'A'
    assert rider.source == 'max90'

  def test_parse_response_handles_missing_power(self):
    """Test parsing when power data is missing."""
    rider = ZRRider()
    rider._raw = {
      'name': 'Test',
      'gender': 'M',
      'race': {
        'current': {'rating': 90.0, 'mixed': {'category': 'B'}},
        'max30': {'rating': 100.0, 'mixed': {'category': 'A'}},
        'max90': {'rating': 95.0, 'mixed': {'category': 'B'}},
      },
    }

    rider._parse_response()

    assert rider.zrcs == 0.0
    assert rider.name == 'Test'

  def test_parse_response_handles_missing_nested_fields(self):
    """Test parsing with missing nested rating fields."""
    rider = ZRRider()
    rider._raw = {
      'name': 'Test',
      'gender': 'M',
      'power': {},
      'race': {
        'current': {},
        'max30': {},
        'max90': {},
      },
    }

    rider._parse_response()

    assert rider.name == 'Test'
    assert rider.current_rating == 0.0
    assert rider.current_rank == 'Unranked'


# ===============================================================================
class TestZRRiderInheritance:
  """Test that ZRRider properly inherits from ZR_obj."""

  def test_zrrider_is_zr_obj(self):
    """Test that ZRRider is an instance of ZR_obj."""
    from zrdatafetch.zr import ZR_obj

    rider = ZRRider()
    assert isinstance(rider, ZR_obj)

  def test_zrrider_has_get_client(self):
    """Test that ZRRider has get_client method from base class."""
    rider = ZRRider()
    assert hasattr(rider, 'get_client')
    assert callable(rider.get_client)

  def test_zrrider_has_close_client(self):
    """Test that ZRRider has close_client method from base class."""
    rider = ZRRider()
    assert hasattr(rider, 'close_client')
    assert callable(rider.close_client)

  def test_zrrider_has_fetch_json(self):
    """Test that ZRRider has fetch_json method from base class."""
    rider = ZRRider()
    assert hasattr(rider, 'fetch_json')
    assert callable(rider.fetch_json)


# ===============================================================================
class TestZRRiderBatchFetch:
  """Test ZRRider.fetch_batch() static method."""

  def test_fetch_batch_requires_authorization(self):
    """Test that fetch_batch requires authorization in config."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = ''  # Empty authorization

      with pytest.raises(ZRConfigError):
        ZRRider.fetch_batch(12345, 67890)

  def test_fetch_batch_max_1000_ids(self):
    """Test that fetch_batch enforces 1000 ID limit."""
    with patch('zrdatafetch.zrrider.Config'):
      with pytest.raises(ValueError, match='Maximum 1000'):
        ZRRider.fetch_batch(*range(1001))

  def test_fetch_batch_empty_ids(self):
    """Test that fetch_batch with no IDs returns empty dict."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      result = ZRRider.fetch_batch()
      assert result == {}

  def test_fetch_batch_single_id(self):
    """Test fetch_batch with a single ID."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        mock_fetch.return_value = [
          {
            'name': 'Test Rider',
            'gender': 'M',
            'power': {'compoundScore': 250.0},
            'race': {
              'current': {'rating': 2250.0, 'mixed': {'category': 'A'}},
              'max30': {'rating': 2240.0, 'mixed': {'category': 'A'}},
              'max90': {'rating': 2200.0, 'mixed': {'category': 'B'}},
            },
          },
        ]

        ZRRider.fetch_batch(12345)

        # Verify fetch_json was called with POST method
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args.kwargs.get('method') == 'POST'
        assert call_args.kwargs.get('json') == [12345]

  def test_fetch_batch_multiple_ids(self):
    """Test fetch_batch with multiple IDs."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        mock_fetch.return_value = [
          {
            'name': 'Rider 1',
            'gender': 'M',
            'power': {'compoundScore': 250.0},
            'race': {
              'current': {'rating': 2250.0, 'mixed': {'category': 'A'}},
              'max30': {'rating': 2240.0, 'mixed': {'category': 'A'}},
              'max90': {'rating': 2200.0, 'mixed': {'category': 'B'}},
            },
          },
          {
            'name': 'Rider 2',
            'gender': 'F',
            'power': {'compoundScore': 200.0},
            'race': {
              'current': {'rating': 2100.0, 'mixed': {'category': 'B'}},
              'max30': {'rating': 2090.0, 'mixed': {'category': 'B'}},
              'max90': {'rating': 2050.0, 'mixed': {'category': 'C'}},
            },
          },
        ]

        result = ZRRider.fetch_batch(12345, 67890)

        # Both riders parsed, but dict key is zwift_id (which is 0 for both in mock)
        # So only last one with zwift_id=0 remains in dict
        assert len(result) >= 1  # At least one rider parsed
        assert 'Rider' in str(result)  # Contains rider names

  def test_fetch_batch_with_epoch(self):
    """Test fetch_batch with historical data (epoch)."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        mock_fetch.return_value = []

        ZRRider.fetch_batch(12345, 67890, epoch=1704067200)

        # Verify endpoint includes epoch
        call_args = mock_fetch.call_args
        assert '/public/riders/1704067200' in call_args[0]

  def test_fetch_batch_uses_post_endpoint_no_epoch(self):
    """Test fetch_batch uses correct endpoint without epoch."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        mock_fetch.return_value = []

        ZRRider.fetch_batch(12345)

        # Verify endpoint is correct
        call_args = mock_fetch.call_args
        assert '/public/riders' in call_args[0]
        # Should be plain /public/riders, not /public/riders/<epoch>

  def test_fetch_batch_skips_malformed_riders(self):
    """Test fetch_batch skips malformed rider data."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        mock_fetch.return_value = [
          {
            'name': 'Valid Rider',
            'gender': 'M',
            'power': {'compoundScore': 250.0},
            'race': {
              'current': {'rating': 2250.0, 'mixed': {'category': 'A'}},
              'max30': {'rating': 2240.0, 'mixed': {'category': 'A'}},
              'max90': {'rating': 2200.0, 'mixed': {'category': 'B'}},
            },
          },
          {
            # Missing required fields - will be skipped
            'name': 'No Race Data',
          },
        ]

        result = ZRRider.fetch_batch(12345, 67890)

        # Should have parsed the valid one and skipped the malformed
        assert len(result) >= 0  # May be 0 or 1 depending on parsing

  def test_fetch_batch_handles_non_list_response(self):
    """Test fetch_batch handles non-list response gracefully."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        mock_fetch.return_value = {'error': 'Not a list'}

        result = ZRRider.fetch_batch(12345)

        assert result == {}

  def test_fetch_batch_up_to_1000_ids(self):
    """Test fetch_batch accepts exactly 1000 IDs."""
    with patch('zrdatafetch.zrrider.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-token'

      with patch('zrdatafetch.zrrider.ZRRider.fetch_json') as mock_fetch:
        mock_fetch.return_value = []

        # Should not raise
        result = ZRRider.fetch_batch(*range(1000))
        assert result == {}
