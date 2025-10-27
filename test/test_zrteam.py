"""Tests for ZRTeam and ZRTeamRider classes.

Tests the team roster data structures and fetching functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from zrdatafetch import ZRTeam, ZRTeamRider
from zrdatafetch.exceptions import ZRConfigError


# ===============================================================================
class TestZRTeamRiderInitialization:
  """Test ZRTeamRider initialization."""

  def test_zrteam_rider_creation(self):
    """Test creating a ZRTeamRider."""
    rider = ZRTeamRider(zwift_id=12345, name="John Doe", gender="M")
    assert rider.zwift_id == 12345
    assert rider.name == "John Doe"
    assert rider.gender == "M"

  def test_zrteam_rider_defaults(self):
    """Test ZRTeamRider default values."""
    rider = ZRTeamRider()
    assert rider.zwift_id == 0
    assert rider.name == ""
    assert rider.gender == "M"
    assert rider.height == 0.0
    assert rider.weight == 0.0
    assert rider.current_rating == 0.0
    assert rider.power_cs == 0.0

  def test_zrteam_rider_with_all_values(self):
    """Test ZRTeamRider with all values."""
    rider = ZRTeamRider(
      zwift_id=12345,
      name="John Doe",
      gender="M",
      height=180.0,
      weight=75.0,
      current_rating=2250.0,
      current_category_mixed="A",
      power_cp=400.0,
      power_cs=250.0,
    )
    assert rider.zwift_id == 12345
    assert rider.name == "John Doe"
    assert rider.gender == "M"
    assert rider.height == 180.0
    assert rider.weight == 75.0
    assert rider.current_rating == 2250.0
    assert rider.current_category_mixed == "A"
    assert rider.power_cp == 400.0
    assert rider.power_cs == 250.0

  def test_zrteam_rider_to_dict(self):
    """Test ZRTeamRider.to_dict()."""
    rider = ZRTeamRider(
      zwift_id=12345,
      name="John Doe",
      current_rating=2250.0,
    )
    d = rider.to_dict()
    assert d["zwift_id"] == 12345
    assert d["name"] == "John Doe"
    assert d["current_rating"] == 2250.0
    assert "height" in d
    assert "power_cp" in d


# ===============================================================================
class TestZRTeamInitialization:
  """Test ZRTeam initialization."""

  def test_zrteam_creation(self):
    """Test creating a ZRTeam."""
    team = ZRTeam(team_id=456)
    assert team.team_id == 456
    assert team.team_name == ""
    assert team.riders == []

  def test_zrteam_defaults(self):
    """Test ZRTeam default values."""
    team = ZRTeam()
    assert team.team_id == 0
    assert team.team_name == ""
    assert team.riders == []

  def test_zrteam_with_riders(self):
    """Test ZRTeam with initial riders."""
    r1 = ZRTeamRider(zwift_id=1, name="Rider 1")
    r2 = ZRTeamRider(zwift_id=2, name="Rider 2")
    team = ZRTeam(team_id=456, team_name="Test Team", riders=[r1, r2])
    assert team.team_id == 456
    assert team.team_name == "Test Team"
    assert len(team.riders) == 2
    assert team.riders[0].zwift_id == 1
    assert team.riders[1].zwift_id == 2


# ===============================================================================
class TestZRTeamIsZRObj:
  """Test that ZRTeam inherits from ZR_obj."""

  def test_zrteam_is_zr_obj(self):
    """Test that ZRTeam is a ZR_obj."""
    from zrdatafetch.zr import ZR_obj

    team = ZRTeam()
    assert isinstance(team, ZR_obj)

  def test_zrteam_has_get_client(self):
    """Test that ZRTeam has get_client method."""
    team = ZRTeam()
    assert hasattr(team, "get_client")
    assert callable(team.get_client)

  def test_zrteam_has_close_client(self):
    """Test that ZRTeam has close_client method."""
    team = ZRTeam()
    assert hasattr(team, "close_client")
    assert callable(team.close_client)

  def test_zrteam_has_fetch_json(self):
    """Test that ZRTeam has fetch_json method."""
    team = ZRTeam()
    assert hasattr(team, "fetch_json")
    assert callable(team.fetch_json)


# ===============================================================================
class TestZRTeamFetch:
  """Test ZRTeam.fetch() method."""

  def test_fetch_requires_team_id(self):
    """Test that fetch with no team_id returns early."""
    team = ZRTeam()
    # Should not raise error, just return early
    team.fetch()
    assert len(team.riders) == 0

  def test_fetch_requires_authorization(self):
    """Test that fetch requires authorization in config."""
    team = ZRTeam(team_id=456)

    with patch("zrdatafetch.zrteam.Config") as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = ""  # Empty authorization

      with pytest.raises(ZRConfigError):
        team.fetch()

  def test_fetch_with_valid_team_id_no_auth(self):
    """Test fetch with team_id but no authorization."""
    team = ZRTeam(team_id=456)

    with patch("zrdatafetch.zrteam.Config") as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = ""

      with pytest.raises(ZRConfigError):
        team.fetch()

  def test_fetch_calls_fetch_json_with_correct_endpoint(self):
    """Test that fetch calls fetch_json with correct endpoint."""
    team = ZRTeam(team_id=456)

    with patch("zrdatafetch.zrteam.Config") as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = "test-auth-header"

      with patch.object(team, "fetch_json", return_value={}):
        team.fetch()
        team.fetch_json.assert_called_once()
        call_args = team.fetch_json.call_args
        assert "/public/clubs/456/0" in call_args[0]

  def test_fetch_with_team_id_parameter(self):
    """Test fetch with team_id parameter."""
    team = ZRTeam()

    with patch("zrdatafetch.zrteam.Config") as mock_config_class:
      mock_config = MagicMock()
      mock_config_class.return_value = mock_config
      mock_config.authorization = "test-auth-header"

      with patch.object(team, "fetch_json", return_value={}):
        team.fetch(team_id=456)
        assert team.team_id == 456


# ===============================================================================
class TestZRTeamParseResponse:
  """Test ZRTeam._parse_response() method."""

  def test_parse_response_empty(self):
    """Test parsing empty response."""
    team = ZRTeam(team_id=456)
    team._raw = {}
    team._parse_response()
    assert len(team.riders) == 0

  def test_parse_response_with_error_message(self):
    """Test parsing response with error message."""
    team = ZRTeam(team_id=456)
    team._raw = {"message": "Team not found"}
    team._parse_response()
    assert len(team.riders) == 0

  def test_parse_response_with_team_name_only(self):
    """Test parsing response with team name but no riders."""
    team = ZRTeam(team_id=456)
    team._raw = {"name": "Test Team", "riders": []}
    team._parse_response()

    assert team.team_name == "Test Team"
    assert len(team.riders) == 0

  def test_parse_response_with_valid_data(self):
    """Test parsing response with valid team data."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Test Team",
      "riders": [
        {
          "riderId": 12345,
          "name": "Rider One",
          "gender": "M",
          "height": 180.0,
          "weight": 75.0,
          "race": {
            "current": {
              "rating": 2250.0,
              "mixed": {"category": "A"},
              "womens": {"category": "A"},
            },
            "max30": {
              "rating": 2240.0,
              "mixed": {"category": "A"},
            },
            "max90": {
              "rating": 2200.0,
              "mixed": {"category": "A"},
            },
          },
          "power": {
            "AWC": 20.0,
            "CP": 400.0,
            "compoundScore": 250.0,
          },
        },
      ],
    }
    team._parse_response()

    assert team.team_name == "Test Team"
    assert len(team.riders) == 1
    assert team.riders[0].zwift_id == 12345
    assert team.riders[0].name == "Rider One"
    assert team.riders[0].current_rating == 2250.0
    assert team.riders[0].power_cp == 400.0

  def test_parse_response_missing_nested_fields(self):
    """Test parsing response with missing nested fields."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Test Team",
      "riders": [
        {
          "riderId": 12345,
          "name": "Rider One",
          # Missing gender, race, power - should use defaults
        },
      ],
    }
    team._parse_response()

    assert len(team.riders) == 1
    assert team.riders[0].zwift_id == 12345
    assert team.riders[0].gender == "M"
    assert team.riders[0].current_rating == 0.0
    assert team.riders[0].power_cp == 0.0

  def test_parse_response_partial_power_data(self):
    """Test parsing response with partial power data."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Test Team",
      "riders": [
        {
          "riderId": 12345,
          "name": "Rider One",
          "power": {
            "CP": 400.0,
            "compoundScore": 250.0,
            # Missing other power metrics
          },
        },
      ],
    }
    team._parse_response()

    assert len(team.riders) == 1
    assert team.riders[0].power_cp == 400.0
    assert team.riders[0].power_cs == 250.0
    assert team.riders[0].power_awc == 0.0  # Missing, so default

  def test_parse_response_malformed_data(self):
    """Test parsing response with malformed rider data."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Test Team",
      "riders": [
        {
          "riderId": 12345,
          "name": "Rider One",
          "height": "not_a_number",  # Will cause ValueError
        },
        {
          "riderId": 67890,
          "name": "Rider Two",
        },
      ],
    }
    team._parse_response()

    # Should have parsed valid rider and skipped malformed one
    assert len(team.riders) == 1
    assert team.riders[0].zwift_id == 67890

  def test_parse_response_invalid_type(self):
    """Test parsing response that's not a dict."""
    team = ZRTeam(team_id=456)
    team._raw = []  # List instead of dict
    team._parse_response()
    # Should handle gracefully
    assert len(team.riders) == 0

  def test_parse_response_invalid_riders_type(self):
    """Test parsing when riders is not a list."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Test Team",
      "riders": "not a list",
    }
    team._parse_response()
    # Should handle gracefully
    assert len(team.riders) == 0

  def test_parse_response_with_all_power_metrics(self):
    """Test parsing response with all power metrics."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Test Team",
      "riders": [
        {
          "riderId": 12345,
          "name": "Rider One",
          "power": {
            "AWC": 20.0,
            "CP": 400.0,
            "compoundScore": 250.0,
            "w5": 2500.0,
            "w15": 1800.0,
            "w30": 1200.0,
            "w60": 900.0,
            "w120": 600.0,
            "w300": 350.0,
            "w1200": 250.0,
            "wkg5": 33.3,
            "wkg15": 24.0,
            "wkg30": 16.0,
            "wkg60": 12.0,
            "wkg120": 8.0,
            "wkg300": 4.7,
            "wkg1200": 3.3,
          },
        },
      ],
    }
    team._parse_response()

    assert len(team.riders) == 1
    rider = team.riders[0]
    assert rider.power_awc == 20.0
    assert rider.power_cp == 400.0
    assert rider.power_w5 == 2500.0
    assert rider.power_wkg1200 == 3.3


# ===============================================================================
class TestZRTeamSerialization:
  """Test ZRTeam serialization methods."""

  def test_to_dict(self):
    """Test ZRTeam.to_dict()."""
    r1 = ZRTeamRider(zwift_id=12345, name="Rider 1")
    r2 = ZRTeamRider(zwift_id=67890, name="Rider 2")
    team = ZRTeam(team_id=456, team_name="Test Team", riders=[r1, r2])

    d = team.to_dict()
    assert d["team_id"] == 456
    assert d["team_name"] == "Test Team"
    assert len(d["riders"]) == 2
    assert d["riders"][0]["zwift_id"] == 12345
    assert d["riders"][1]["zwift_id"] == 67890

  def test_to_dict_empty(self):
    """Test to_dict with no riders."""
    team = ZRTeam(team_id=456, team_name="Empty Team")
    d = team.to_dict()
    assert d["team_id"] == 456
    assert d["team_name"] == "Empty Team"
    assert d["riders"] == []

  def test_json_output(self):
    """Test JSON serialization."""
    team = ZRTeam(team_id=456, team_name="Test Team")
    team.riders = [ZRTeamRider(zwift_id=12345, name="Rider One")]

    json_str = team.json()
    assert isinstance(json_str, str)
    assert "456" in json_str
    assert "Test Team" in json_str
    assert "12345" in json_str


# ===============================================================================
class TestZRTeamIntegration:
  """Test ZRTeam integration scenarios."""

  def test_multiple_riders_in_team(self):
    """Test handling multiple riders in a single team."""
    team = ZRTeam(team_id=456, team_name="Large Team")

    # Simulate 50 team members
    riders_data = [
      {
        "riderId": i,
        "name": f"Rider {i}",
        "gender": "M" if i % 2 == 0 else "F",
        "height": 170.0 + i,
        "weight": 70.0 + i % 10,
        "race": {
          "current": {
            "rating": 2000.0 + i * 10,
            "mixed": {"category": chr(65 + (i % 5))},  # A-E
          },
        },
      }
      for i in range(1, 51)
    ]

    team._raw = {"name": "Large Team", "riders": riders_data}
    team._parse_response()

    assert len(team.riders) == 50
    assert team.riders[0].zwift_id == 1
    assert team.riders[0].current_rating == 2010.0
    assert team.riders[49].zwift_id == 50
    assert team.riders[49].current_rating == 2500.0

  def test_women_category_handling(self):
    """Test handling of women's category data."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Mixed Team",
      "riders": [
        {
          "riderId": 1,
          "name": "Woman Rider",
          "gender": "F",
          "race": {
            "current": {
              "rating": 2100.0,
              "mixed": {"category": "B"},
              "womens": {"category": "A"},
            },
          },
        },
      ],
    }
    team._parse_response()

    assert len(team.riders) == 1
    assert team.riders[0].gender == "F"
    assert team.riders[0].current_category_mixed == "B"
    assert team.riders[0].current_category_womens == "A"

  def test_rating_progression_across_timeframes(self):
    """Test tracking rating progression across current/max30/max90."""
    team = ZRTeam(team_id=456)
    team._raw = {
      "name": "Test Team",
      "riders": [
        {
          "riderId": 12345,
          "name": "Rider One",
          "race": {
            "current": {"rating": 2250.0, "mixed": {"category": "A"}},
            "max30": {"rating": 2240.0, "mixed": {"category": "A"}},
            "max90": {"rating": 2200.0, "mixed": {"category": "B"}},
          },
        },
      ],
    }
    team._parse_response()

    rider = team.riders[0]
    assert rider.current_rating == 2250.0
    assert rider.max30_rating == 2240.0
    assert rider.max90_rating == 2200.0
    assert rider.current_category_mixed == "A"
    assert rider.max30_category_mixed == "A"
    assert rider.max90_category_mixed == "B"
