"""Tests for ZRRider dataclass parsing."""

import json
from pathlib import Path

import pytest

from zrdatafetch.zrrider import ZRRider

FIXTURE_PATH = Path(__file__).parent.parent / 'fixtures' / 'zr_rider_550564.json'


@pytest.fixture
def rider_data() -> dict:
  """Load rider fixture data."""
  with open(FIXTURE_PATH, encoding='utf-8') as f:
    return json.load(f)


@pytest.fixture
def rider(rider_data: dict) -> ZRRider:
  """Create ZRRider from fixture data."""
  return ZRRider.from_dict(rider_data)


class TestZRRiderBasicFields:
  """Test basic rider fields."""

  def test_zwift_id(self, rider: ZRRider) -> None:
    assert rider.zwift_id == 550564

  def test_name(self, rider: ZRRider) -> None:
    assert rider.name == 'Doug Morris [TeamDIRT.racing]'

  def test_gender(self, rider: ZRRider) -> None:
    assert rider.gender == 'M'

  def test_zrcs(self, rider: ZRRider) -> None:
    assert rider.zrcs == pytest.approx(857.699, rel=1e-3)

  def test_current_rating(self, rider: ZRRider) -> None:
    assert rider.current_rating == pytest.approx(911.875, rel=1e-3)

  def test_current_rank(self, rider: ZRRider) -> None:
    assert rider.current_rank == 'Silver'

  def test_max30_rating(self, rider: ZRRider) -> None:
    assert rider.max30_rating == pytest.approx(911.875, rel=1e-3)

  def test_max30_rank(self, rider: ZRRider) -> None:
    assert rider.max30_rank == 'Silver'

  def test_max90_rating(self, rider: ZRRider) -> None:
    assert rider.max90_rating == pytest.approx(911.875, rel=1e-3)

  def test_max90_rank(self, rider: ZRRider) -> None:
    assert rider.max90_rank == 'Silver'


class TestZRRiderRaceStats:
  """Test race stats fields."""

  def test_race_finishes(self, rider: ZRRider) -> None:
    assert rider.race_finishes == 13

  def test_race_dnfs(self, rider: ZRRider) -> None:
    assert rider.race_dnfs == 0

  def test_race_wins(self, rider: ZRRider) -> None:
    assert rider.race_wins == 1

  def test_race_podiums(self, rider: ZRRider) -> None:
    assert rider.race_podiums == 3


class TestZRRiderHandicaps:
  """Test handicap fields."""

  def test_handicap_flat(self, rider: ZRRider) -> None:
    assert rider.handicap_flat == pytest.approx(72.047, rel=1e-3)

  def test_handicap_rolling(self, rider: ZRRider) -> None:
    assert rider.handicap_rolling == pytest.approx(-90.916, rel=1e-3)

  def test_handicap_hilly(self, rider: ZRRider) -> None:
    assert rider.handicap_hilly == pytest.approx(-137.232, rel=1e-3)

  def test_handicap_mountainous(self, rider: ZRRider) -> None:
    assert rider.handicap_mountainous == pytest.approx(-151.229, rel=1e-3)


class TestZRRiderPhenotype:
  """Test phenotype fields."""

  def test_phenotype(self, rider: ZRRider) -> None:
    assert rider.phenotype == 'Sprinter'

  def test_phenotype_bias(self, rider: ZRRider) -> None:
    assert rider.phenotype_bias == pytest.approx(32.95)

  def test_phenotype_sprinter(self, rider: ZRRider) -> None:
    assert rider.phenotype_sprinter == pytest.approx(94.0)

  def test_phenotype_puncheur(self, rider: ZRRider) -> None:
    assert rider.phenotype_puncheur == pytest.approx(68.6)

  def test_phenotype_pursuiter(self, rider: ZRRider) -> None:
    assert rider.phenotype_pursuiter == pytest.approx(43.4)

  def test_phenotype_climber(self, rider: ZRRider) -> None:
    assert rider.phenotype_climber == pytest.approx(38.2)

  def test_phenotype_tt(self, rider: ZRRider) -> None:
    assert rider.phenotype_tt == pytest.approx(78.1)


class TestZRRiderSeed:
  """Test seed fields."""

  def test_seed_race(self, rider: ZRRider) -> None:
    assert rider.seed_race == pytest.approx(425.765, rel=1e-3)

  def test_seed_time_trial(self, rider: ZRRider) -> None:
    assert rider.seed_time_trial == pytest.approx(434.759, rel=1e-3)

  def test_seed_endurance(self, rider: ZRRider) -> None:
    assert rider.seed_endurance == pytest.approx(386.0)

  def test_seed_pursuit(self, rider: ZRRider) -> None:
    assert rider.seed_pursuit == pytest.approx(397.0)

  def test_seed_sprint(self, rider: ZRRider) -> None:
    assert rider.seed_sprint == pytest.approx(544.5)

  def test_seed_punch(self, rider: ZRRider) -> None:
    assert rider.seed_punch == pytest.approx(479.61)

  def test_seed_climb(self, rider: ZRRider) -> None:
    assert rider.seed_climb == pytest.approx(394.5)

  def test_seed_time_trial_factor(self, rider: ZRRider) -> None:
    assert rider.seed_time_trial_factor == pytest.approx(476.0)


class TestZRRiderVelo:
  """Test vELO2 fields."""

  def test_velo_race(self, rider: ZRRider) -> None:
    assert rider.velo_race == pytest.approx(432.731, rel=1e-3)

  def test_velo_time_trial(self, rider: ZRRider) -> None:
    assert rider.velo_time_trial == pytest.approx(441.610, rel=1e-3)

  def test_velo_endurance(self, rider: ZRRider) -> None:
    assert rider.velo_endurance == pytest.approx(403.454, rel=1e-3)

  def test_velo_pursuit(self, rider: ZRRider) -> None:
    assert rider.velo_pursuit == pytest.approx(400.027, rel=1e-3)

  def test_velo_sprint(self, rider: ZRRider) -> None:
    assert rider.velo_sprint == pytest.approx(549.366, rel=1e-3)

  def test_velo_punch(self, rider: ZRRider) -> None:
    assert rider.velo_punch == pytest.approx(483.392, rel=1e-3)

  def test_velo_climb(self, rider: ZRRider) -> None:
    assert rider.velo_climb == pytest.approx(386.251, rel=1e-3)

  def test_velo_time_trial_factor(self, rider: ZRRider) -> None:
    assert rider.velo_time_trial_factor == pytest.approx(479.0)


class TestZRRiderVeloSkill:
  """Test vELO2 skill fields (gh#17)."""

  def test_velo_skill_endurance(self, rider: ZRRider) -> None:
    assert rider.velo_skill_endurance == pytest.approx(0.0)

  def test_velo_skill_pursuit(self, rider: ZRRider) -> None:
    assert rider.velo_skill_pursuit == pytest.approx(0.0)

  def test_velo_skill_sprint(self, rider: ZRRider) -> None:
    assert rider.velo_skill_sprint == pytest.approx(0.3206484167583312)

  def test_velo_skill_punch(self, rider: ZRRider) -> None:
    assert rider.velo_skill_punch == pytest.approx(0.0)

  def test_velo_skill_climb(self, rider: ZRRider) -> None:
    assert rider.velo_skill_climb == pytest.approx(0.0)

  def test_velo_skill_time_trial(self, rider: ZRRider) -> None:
    assert rider.velo_skill_time_trial == pytest.approx(0.0)


class TestZRRiderVeloCategory:
  """Test vELO2 category fields (gh#17)."""

  def test_velo_category_number(self, rider: ZRRider) -> None:
    assert rider.velo_category_number == 8

  def test_velo_category_name(self, rider: ZRRider) -> None:
    assert rider.velo_category_name == 'Silver'


class TestZRRiderVeloMax30:
  """Test vELO2 max30 fields (gh#17)."""

  def test_velo_max30(self, rider: ZRRider) -> None:
    assert rider.velo_max30 == 434.86035000000004

  def test_velo_max30_category_number(self, rider: ZRRider) -> None:
    assert rider.velo_max30_category_number == 8

  def test_velo_max30_category_name(self, rider: ZRRider) -> None:
    assert rider.velo_max30_category_name == 'Silver'


class TestZRRiderVeloMax90:
  """Test vELO2 max90 fields (gh#17)."""

  def test_velo_max90(self, rider: ZRRider) -> None:
    assert rider.velo_max90 == 453.5100245027948

  def test_velo_max90_category_number(self, rider: ZRRider) -> None:
    assert rider.velo_max90_category_number == 8

  def test_velo_max90_category_name(self, rider: ZRRider) -> None:
    assert rider.velo_max90_category_name == 'Silver'


class TestZRRiderExtraFields:
  """Test that unmodeled fields go to _extra."""

  def test_country_in_extra(self, rider: ZRRider) -> None:
    assert 'country' in rider.extras()

  def test_club_in_extra(self, rider: ZRRider) -> None:
    assert 'club' in rider.extras()

  def test_known_fields_not_in_extra(self, rider: ZRRider) -> None:
    extras = rider.extras()
    for key in (
      'name',
      'gender',
      'race',
      'power',
      'riderId',
      'handicaps',
      'phenotype',
      'seed',
      'velo',
    ):
      assert key not in extras

  def test_velo_not_in_extras_or_excluded(self, rider: ZRRider) -> None:
    assert 'velo' not in rider.extras()
    assert 'velo' not in rider.excluded()


class TestZRRiderAsDict:
  """Test asdict includes new fields."""

  def test_asdict_has_velo_race(self, rider: ZRRider) -> None:
    d = rider.asdict()
    assert 'velo_race' in d
    assert d['velo_race'] == pytest.approx(432.731, rel=1e-3)

  def test_asdict_has_seed_race(self, rider: ZRRider) -> None:
    d = rider.asdict()
    assert 'seed_race' in d

  def test_asdict_has_handicap_flat(self, rider: ZRRider) -> None:
    d = rider.asdict()
    assert 'handicap_flat' in d

  def test_asdict_has_phenotype(self, rider: ZRRider) -> None:
    d = rider.asdict()
    assert d['phenotype'] == 'Sprinter'

  def test_asdict_excludes_private(self, rider: ZRRider) -> None:
    d = rider.asdict()
    assert '_extra' not in d
    assert '_excluded' not in d

  def test_asdict_has_new_velo_fields(self, rider: ZRRider) -> None:
    d = rider.asdict()
    for key in (
      'velo_skill_endurance',
      'velo_skill_pursuit',
      'velo_skill_sprint',
      'velo_skill_punch',
      'velo_skill_climb',
      'velo_skill_time_trial',
      'velo_category_number',
      'velo_category_name',
    ):
      assert key in d
    assert d['velo_skill_sprint'] == pytest.approx(0.3206484167583312)
    assert d['velo_category_number'] == 8
    assert d['velo_category_name'] == 'Silver'

  def test_repr_has_new_velo_fields(self, rider: ZRRider) -> None:
    text = repr(rider)
    assert 'velo_skill_sprint' in text
    assert 'velo_category_name' in text

  def test_asdict_has_velo_max_fields(self, rider: ZRRider) -> None:
    d = rider.asdict()
    for key in (
      'velo_max30',
      'velo_max90',
      'velo_max30_category_number',
      'velo_max30_category_name',
      'velo_max90_category_number',
      'velo_max90_category_name',
    ):
      assert key in d
    assert d['velo_max30'] == 434.86035000000004
    assert d['velo_max90'] == 453.5100245027948
    assert d['velo_max30_category_number'] == 8
    assert d['velo_max30_category_name'] == 'Silver'

  def test_repr_has_velo_max_fields(self, rider: ZRRider) -> None:
    text = repr(rider)
    assert 'velo_max30' in text
    assert 'velo_max30_category_name' in text


class TestZRRiderMissingFields:
  """Test defaults when optional sections are absent."""

  def test_missing_handicaps(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.handicap_flat == 0.0
    assert rider.handicap_rolling == 0.0

  def test_missing_phenotype(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.phenotype == ''
    assert rider.phenotype_sprinter == 0.0

  def test_missing_seed(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.seed_race == 0.0
    assert rider.seed_sprint == 0.0

  def test_missing_velo(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_race == 0.0
    assert rider.velo_sprint == 0.0

  def test_missing_race_stats(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.race_finishes == 0
    assert rider.race_wins == 0

  def test_missing_velo_skill(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_skill_sprint == 0.0
    assert rider.velo_skill_endurance == 0.0

  def test_missing_velo_category(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_category_number == 0
    assert rider.velo_category_name == ''

  def test_velo_without_skill_or_category(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
      'velo': {'race': 100.0, 'factors': {'sprint': 200.0}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_race == pytest.approx(100.0)
    assert rider.velo_skill_sprint == 0.0
    assert rider.velo_category_number == 0
    assert rider.velo_category_name == ''

  def test_malformed_velo_skill_category(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
      'velo': {
        'skill': {'sprint': 'not-a-number'},
        'category': {'number': 'not-a-number', 'name': None},
      },
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_skill_sprint == 0.0
    assert rider.velo_category_number == 0
    assert rider.velo_category_name == ''

  def test_missing_velo_max_fields(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_max30 == 0.0
    assert rider.velo_max90 == 0.0
    assert rider.velo_max30_category_number == 0
    assert rider.velo_max30_category_name == ''
    assert rider.velo_max90_category_number == 0
    assert rider.velo_max90_category_name == ''

  def test_velo_without_max_fields(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
      'velo': {'race': 100.0, 'factors': {'sprint': 200.0}},
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_race == pytest.approx(100.0)
    assert rider.velo_max30 == 0.0
    assert rider.velo_max30_category_number == 0
    assert rider.velo_max30_category_name == ''

  def test_malformed_velo_max_fields(self) -> None:
    data = {
      'riderId': 1,
      'name': 'Test',
      'race': {'current': {'rating': 100, 'mixed': {'category': 'Bronze'}}},
      'velo': {
        'max30': 'not-a-number',
        'max90': None,
        'max30Category': {'number': 'not-a-number', 'name': None},
        'max90Category': {'number': None, 'name': None},
      },
    }
    rider = ZRRider.from_dict(data)
    assert rider.velo_max30 == 0.0
    assert rider.velo_max90 == 0.0
    assert rider.velo_max30_category_number == 0
    assert rider.velo_max30_category_name == ''
    assert rider.velo_max90_category_number == 0
    assert rider.velo_max90_category_name == ''
