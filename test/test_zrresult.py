"""Tests for ZRResult and ZRRiderResult classes.

Tests the race result data structures and fetching functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from zrdatafetch import ZRResult, ZRRiderResult
from zrdatafetch.exceptions import ZRConfigError


# ===============================================================================
class TestZRRiderResultInitialization:
  """Test ZRRiderResult initialization."""

  def test_zrrider_result_creation(self):
    """Test creating a ZRRiderResult."""
    result = ZRRiderResult(zwift_id=12345, position=1, gap=0.0)
    assert result.zwift_id == 12345
    assert result.position == 1
    assert result.gap == 0.0

  def test_zrrider_result_defaults(self):
    """Test ZRRiderResult default values."""
    result = ZRRiderResult()
    assert result.zwift_id == 0
    assert result.position == 0
    assert result.category == ''
    assert result.time == 0.0
    assert result.gap == 0.0
    assert result.rating_before == 0.0
    assert result.rating == 0.0
    assert result.rating_delta == 0.0

  def test_zrrider_result_with_all_values(self):
    """Test ZRRiderResult with all values."""
    result = ZRRiderResult(
      zwift_id=12345,
      position=5,
      position_in_category=3,
      category='B',
      time=1234.5,
      gap=45.2,
      rating_before=2200.0,
      rating=2210.5,
      rating_delta=10.5,
    )
    assert result.zwift_id == 12345
    assert result.position == 5
    assert result.position_in_category == 3
    assert result.category == 'B'
    assert result.time == 1234.5
    assert result.gap == 45.2
    assert result.rating_before == 2200.0
    assert result.rating == 2210.5
    assert result.rating_delta == 10.5

  def test_zrrider_result_to_dict(self):
    """Test ZRRiderResult.to_dict()."""
    result = ZRRiderResult(zwift_id=12345, position=1, category='A')
    d = result.to_dict()
    assert d['zwift_id'] == 12345
    assert d['position'] == 1
    assert d['category'] == 'A'
    assert 'gap' in d
    assert 'rating_delta' in d


# ===============================================================================
class TestZRResultInitialization:
  """Test ZRResult initialization."""

  def test_zrresult_creation(self):
    """Test creating a ZRResult."""
    result = ZRResult(race_id=3590800)
    assert result.race_id == 3590800
    assert result.results == []

  def test_zrresult_defaults(self):
    """Test ZRResult default values."""
    result = ZRResult()
    assert result.race_id == 0
    assert result.results == []

  def test_zrresult_with_results(self):
    """Test ZRResult with initial results."""
    r1 = ZRRiderResult(zwift_id=1, position=1)
    r2 = ZRRiderResult(zwift_id=2, position=2)
    result = ZRResult(race_id=3590800, results=[r1, r2])
    assert result.race_id == 3590800
    assert len(result.results) == 2
    assert result.results[0].zwift_id == 1
    assert result.results[1].zwift_id == 2


# ===============================================================================
class TestZRResultIsZRObj:
  """Test that ZRResult inherits from ZR_obj."""

  def test_zrresult_is_zr_obj(self):
    """Test that ZRResult is a ZR_obj."""
    from zrdatafetch.zr import ZR_obj

    result = ZRResult()
    assert isinstance(result, ZR_obj)

  def test_zrresult_has_get_client(self):
    """Test that ZRResult has get_client method."""
    result = ZRResult()
    assert hasattr(result, 'get_client')
    assert callable(result.get_client)

  def test_zrresult_has_close_client(self):
    """Test that ZRResult has close_client method."""
    result = ZRResult()
    assert hasattr(result, 'close_client')
    assert callable(result.close_client)

  def test_zrresult_has_fetch_json(self):
    """Test that ZRResult has fetch_json method."""
    result = ZRResult()
    assert hasattr(result, 'fetch_json')
    assert callable(result.fetch_json)


# ===============================================================================
class TestZRResultFetch:
  """Test ZRResult.fetch() method."""

  def test_fetch_requires_race_id(self):
    """Test that fetch with no race_id returns early."""
    result = ZRResult()
    # Should not raise error, just return early
    result.fetch()
    assert len(result.results) == 0

  def test_fetch_requires_authorization(self):
    """Test that fetch requires authorization in config."""
    result = ZRResult(race_id=3590800)

    with patch('zrdatafetch.zrresult.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = ''  # Empty authorization

      with pytest.raises(ZRConfigError):
        result.fetch()

  def test_fetch_with_valid_race_id_no_auth(self):
    """Test fetch with race_id but no authorization."""
    result = ZRResult(race_id=3590800)

    with patch('zrdatafetch.zrresult.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = ''

      with pytest.raises(ZRConfigError):
        result.fetch()

  def test_fetch_calls_fetch_json_with_correct_endpoint(self):
    """Test that fetch calls fetch_json with correct endpoint."""
    result = ZRResult(race_id=3590800)

    with patch('zrdatafetch.zrresult.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-auth-header'

      with patch.object(result, 'fetch_json', return_value=[]):
        result.fetch()
        result.fetch_json.assert_called_once()
        call_args = result.fetch_json.call_args
        assert '/public/results/3590800' in call_args[0]

  def test_fetch_with_epoch_parameter(self):
    """Test fetch with epoch parameter."""
    result = ZRResult(race_id=3590800)

    with patch('zrdatafetch.zrresult.Config') as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = 'test-auth-header'

      with patch.object(result, 'fetch_json', return_value=[]):
        # Note: ZRResult doesn't use epoch in endpoint, but test for consistency
        result.fetch(race_id=3590800)
        assert result.race_id == 3590800


# ===============================================================================
class TestZRResultParseResponse:
  """Test ZRResult._parse_response() method."""

  def test_parse_response_empty(self):
    """Test parsing empty response."""
    result = ZRResult(race_id=3590800)
    result._raw = []
    result._parse_response()
    assert len(result.results) == 0

  def test_parse_response_with_error_message(self):
    """Test parsing response with error message."""
    result = ZRResult(race_id=3590800)
    result._raw = {'message': 'Race not found'}
    result._parse_response()
    assert len(result.results) == 0

  def test_parse_response_with_valid_data(self):
    """Test parsing response with valid rider results."""
    result = ZRResult(race_id=3590800)
    result._raw = [
      {
        'riderId': 12345,
        'position': 1,
        'category': 'A',
        'time': 1234.5,
        'gap': 0.0,
        'rating': 2250.0,
        'ratingBefore': 2240.0,
        'ratingDelta': 10.0,
      },
      {
        'riderId': 67890,
        'position': 2,
        'category': 'A',
        'time': 1245.3,
        'gap': 10.8,
        'rating': 2200.0,
        'ratingBefore': 2195.0,
        'ratingDelta': 5.0,
      },
    ]
    result._parse_response()

    assert len(result.results) == 2
    assert result.results[0].zwift_id == 12345
    assert result.results[0].position == 1
    assert result.results[0].category == 'A'
    assert result.results[1].zwift_id == 67890
    assert result.results[1].position == 2

  def test_parse_response_missing_fields(self):
    """Test parsing response with missing fields (uses defaults)."""
    result = ZRResult(race_id=3590800)
    result._raw = [
      {
        'riderId': 12345,
        'position': 1,
        # Missing other fields - should use defaults
      },
    ]
    result._parse_response()

    assert len(result.results) == 1
    assert result.results[0].zwift_id == 12345
    assert result.results[0].position == 1
    assert result.results[0].category == ''
    assert result.results[0].gap == 0.0

  def test_parse_response_malformed_data(self):
    """Test parsing response with malformed data (accepts string zwift_id).

    Note: Since zwift_id is not converted with int(), string values are accepted.
    """
    result = ZRResult(race_id=3590800)
    result._raw = [
      {
        'riderId': 12345,
        'position': 1,
        'category': 'A',
      },
      {
        'riderId': 'not_a_number',  # Accepted as-is since int() conversion happens on field
        'position': 2,
      },
      {
        'riderId': 67890,
        'position': 3,
        'category': 'B',
      },
    ]
    result._parse_response()

    # All riders should be parsed since we don't validate zwift_id type
    assert len(result.results) == 3
    assert result.results[0].zwift_id == 12345
    assert result.results[1].zwift_id == 'not_a_number'
    assert result.results[2].zwift_id == 67890

  def test_parse_response_invalid_type(self):
    """Test parsing response that's not a list."""
    result = ZRResult(race_id=3590800)
    result._raw = {'error': 'Not a list'}
    result._parse_response()
    # Should handle gracefully
    assert len(result.results) == 0

  def test_parse_response_none_values(self):
    """Test parsing response with None values for floats.

    Note: None values in numeric fields cause the rider to be skipped
    since float(None) raises TypeError.
    """
    result = ZRResult(race_id=3590800)
    result._raw = [
      {
        'riderId': 12345,
        'position': 1,
        'rating': None,  # None value causes skip
        'gap': None,
      },
    ]
    result._parse_response()

    # Should skip riders with None values in float fields
    assert len(result.results) == 0


# ===============================================================================
class TestZRResultSerialization:
  """Test ZRResult serialization methods."""

  def test_to_dict(self):
    """Test ZRResult.to_dict()."""
    r1 = ZRRiderResult(zwift_id=12345, position=1, rating=2250.0)
    r2 = ZRRiderResult(zwift_id=67890, position=2, rating=2200.0)
    result = ZRResult(race_id=3590800, results=[r1, r2])

    d = result.to_dict()
    assert d['race_id'] == 3590800
    assert len(d['results']) == 2
    assert d['results'][0]['zwift_id'] == 12345
    assert d['results'][1]['zwift_id'] == 67890

  def test_to_dict_empty(self):
    """Test to_dict with no results."""
    result = ZRResult(race_id=3590800)
    d = result.to_dict()
    assert d['race_id'] == 3590800
    assert d['results'] == []

  def test_json_output(self):
    """Test JSON serialization."""
    result = ZRResult(race_id=3590800)
    result.results = [ZRRiderResult(zwift_id=12345, position=1)]

    json_str = result.json()
    assert isinstance(json_str, str)
    assert '3590800' in json_str
    assert '12345' in json_str


# ===============================================================================
class TestZRResultIntegration:
  """Test ZRResult integration scenarios."""

  def test_multiple_results_in_race(self):
    """Test handling multiple results in a single race."""
    result = ZRResult(race_id=3590800)

    # Simulate multiple riders
    riders_data = [
      {'riderId': i, 'position': i, 'category': 'A' if i < 10 else 'B'}
      for i in range(1, 51)  # 50 riders
    ]

    result._raw = riders_data
    result._parse_response()

    assert len(result.results) == 50
    assert result.results[0].zwift_id == 1
    assert result.results[0].position == 1
    assert result.results[49].zwift_id == 50

  def test_rating_changes_across_results(self):
    """Test tracking rating changes for multiple riders."""
    result = ZRResult(race_id=3590800)
    result._raw = [
      {
        'riderId': 1,
        'position': 1,
        'rating': 2250.0,
        'ratingBefore': 2240.0,
        'ratingDelta': 10.0,
      },
      {
        'riderId': 2,
        'position': 2,
        'rating': 2200.0,
        'ratingBefore': 2205.0,
        'ratingDelta': -5.0,
      },
      {
        'riderId': 3,
        'position': 3,
        'rating': 2180.0,
        'ratingBefore': 2175.0,
        'ratingDelta': 5.0,
      },
    ]
    result._parse_response()

    assert len(result.results) == 3
    assert result.results[0].rating_delta == 10.0  # Winner gained rating
    assert result.results[1].rating_delta == -5.0  # Second lost rating
    assert result.results[2].rating_delta == 5.0  # Third gained rating
