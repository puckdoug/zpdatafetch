"""Pure dataclass for Zwiftracing rider data.

This module provides the ZRRider dataclass for representing rider
rating data without any fetch logic. Fetching is handled by ZRRiderFetch.
"""

from dataclasses import asdict, dataclass, field
from typing import Any

from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr_utils import (
  extract_nested_value,
  safe_float,
  safe_int,
  safe_str,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class ZRRider:
  """Rider rating data from Zwiftracing API.

  Represents a rider's current and historical ratings, vELO2 scores,
  handicaps, phenotype, and race stats.

  This is a pure data container with no fetch logic.

  Attributes:
    zwift_id: Rider's Zwift ID
    name: Rider's display name
    gender: Rider's gender (M/F)
    current_rating: Current rating score
    current_rank: Current category rank
    max30_rating: Maximum rating in last 30 days
    max30_rank: Max30 category rank
    max90_rating: Maximum rating in last 90 days
    max90_rank: Max90 category rank
    zrcs: Zwiftracing compound score
    race_finishes: Total race finishes
    race_dnfs: Total DNFs
    race_wins: Total race wins
    race_podiums: Total podium finishes
    handicap_flat: Terrain handicap for flat courses
    handicap_rolling: Terrain handicap for rolling courses
    handicap_hilly: Terrain handicap for hilly courses
    handicap_mountainous: Terrain handicap for mountainous courses
    phenotype: Primary rider phenotype (e.g. "Sprinter")
    phenotype_bias: Phenotype bias score
    phenotype_sprinter: Sprinter score
    phenotype_puncheur: Puncheur score
    phenotype_pursuiter: Pursuiter score
    phenotype_climber: Climber score
    phenotype_tt: Time trial score
    seed_race: Seed race rating
    seed_time_trial: Seed time trial rating
    seed_endurance: Seed endurance factor
    seed_pursuit: Seed pursuit factor
    seed_sprint: Seed sprint factor
    seed_punch: Seed punch factor
    seed_climb: Seed climb factor
    seed_time_trial_factor: Seed time trial factor
    velo_race: vELO2 race rating
    velo_time_trial: vELO2 time trial rating
    velo_endurance: vELO2 endurance factor
    velo_pursuit: vELO2 pursuit factor
    velo_sprint: vELO2 sprint factor
    velo_punch: vELO2 punch factor
    velo_climb: vELO2 climb factor
    velo_time_trial_factor: vELO2 time trial factor
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
  """

  # Public attributes
  zwift_id: int = 0
  name: str = 'Nobody'
  gender: str = 'M'
  current_rating: float = 0.0
  current_rank: str = 'Unranked'
  max30_rating: float = 0.0
  max30_rank: str = 'Unranked'
  max90_rating: float = 0.0
  max90_rank: str = 'Unranked'
  zrcs: float = 0.0

  # Race stats
  race_finishes: int = 0
  race_dnfs: int = 0
  race_wins: int = 0
  race_podiums: int = 0

  # Handicaps (terrain profile adjustments)
  handicap_flat: float = 0.0
  handicap_rolling: float = 0.0
  handicap_hilly: float = 0.0
  handicap_mountainous: float = 0.0

  # Phenotype (rider type classification)
  phenotype: str = ''
  phenotype_bias: float = 0.0
  phenotype_sprinter: float = 0.0
  phenotype_puncheur: float = 0.0
  phenotype_pursuiter: float = 0.0
  phenotype_climber: float = 0.0
  phenotype_tt: float = 0.0

  # Seed (initial rating estimates)
  seed_race: float = 0.0
  seed_time_trial: float = 0.0
  seed_endurance: float = 0.0
  seed_pursuit: float = 0.0
  seed_sprint: float = 0.0
  seed_punch: float = 0.0
  seed_climb: float = 0.0
  seed_time_trial_factor: float = 0.0

  # Velo (vELO2 live ratings)
  velo_race: float = 0.0
  velo_time_trial: float = 0.0
  velo_endurance: float = 0.0
  velo_pursuit: float = 0.0
  velo_sprint: float = 0.0
  velo_punch: float = 0.0
  velo_climb: float = 0.0
  velo_time_trial_factor: float = 0.0

  # Field classification
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRRider':
    """Create instance from API response dict.

    Parses Zwiftracing API response and extracts rider rating fields.
    Unknown fields are captured in _extra for forward compatibility.

    Args:
      data: Dictionary containing rider data from API

    Returns:
      ZRRider instance with parsed fields
    """
    # Known fields that will be extracted
    known_fields = {
      'name',
      'gender',
      'race',
      'power',
      'riderId',
      'zwiftId',
      'handicaps',
      'phenotype',
      'seed',
      'velo',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded: set[str] = set()

    # Check for error in response
    if 'message' in data:
      logger.error(f'API error in rider data: {data["message"]}')
      return cls()

    # Check for required fields
    if 'name' not in data or 'race' not in data:
      logger.warning('Missing required fields (name or race) in response')
      return cls()

    try:
      # Extract using safe utilities
      name = safe_str(data.get('name'), default='Nobody')
      gender = safe_str(data.get('gender'), default='M')

      # ZRCS (compound score)
      zrcs = safe_float(extract_nested_value(data, 'power', 'compoundScore'))

      # Current rating
      current_rating = safe_float(
        extract_nested_value(data, 'race', 'current', 'rating'),
      )
      current_rank = safe_str(
        extract_nested_value(data, 'race', 'current', 'mixed', 'category'),
        default='Unranked',
      )

      # Max90 rating
      max90_rating = safe_float(
        extract_nested_value(data, 'race', 'max90', 'rating'),
      )
      max90_rank = safe_str(
        extract_nested_value(data, 'race', 'max90', 'mixed', 'category'),
        default='Unranked',
      )

      # Max30 rating
      max30_rating = safe_float(
        extract_nested_value(data, 'race', 'max30', 'rating'),
      )
      max30_rank = safe_str(
        extract_nested_value(data, 'race', 'max30', 'mixed', 'category'),
        default='Unranked',
      )

      # Extract zwift_id (try multiple possible field names)
      zwift_id = safe_int(data.get('riderId', data.get('zwiftId')))

      # Race stats
      race_finishes = safe_int(extract_nested_value(data, 'race', 'finishes'))
      race_dnfs = safe_int(extract_nested_value(data, 'race', 'dnfs'))
      race_wins = safe_int(extract_nested_value(data, 'race', 'wins'))
      race_podiums = safe_int(extract_nested_value(data, 'race', 'podiums'))

      # Handicaps
      handicap_flat = safe_float(
        extract_nested_value(data, 'handicaps', 'profile', 'flat'),
      )
      handicap_rolling = safe_float(
        extract_nested_value(data, 'handicaps', 'profile', 'rolling'),
      )
      handicap_hilly = safe_float(
        extract_nested_value(data, 'handicaps', 'profile', 'hilly'),
      )
      handicap_mountainous = safe_float(
        extract_nested_value(data, 'handicaps', 'profile', 'mountainous'),
      )

      # Phenotype
      phenotype_value = safe_str(
        extract_nested_value(data, 'phenotype', 'value'),
        default='',
      )
      phenotype_bias = safe_float(
        extract_nested_value(data, 'phenotype', 'bias'),
      )
      phenotype_sprinter = safe_float(
        extract_nested_value(data, 'phenotype', 'scores', 'sprinter'),
      )
      phenotype_puncheur = safe_float(
        extract_nested_value(data, 'phenotype', 'scores', 'puncheur'),
      )
      phenotype_pursuiter = safe_float(
        extract_nested_value(data, 'phenotype', 'scores', 'pursuiter'),
      )
      phenotype_climber = safe_float(
        extract_nested_value(data, 'phenotype', 'scores', 'climber'),
      )
      phenotype_tt = safe_float(
        extract_nested_value(data, 'phenotype', 'scores', 'tt'),
      )

      # Seed
      seed_race = safe_float(extract_nested_value(data, 'seed', 'race'))
      seed_time_trial = safe_float(
        extract_nested_value(data, 'seed', 'timeTrial'),
      )
      seed_endurance = safe_float(
        extract_nested_value(data, 'seed', 'factors', 'endurance'),
      )
      seed_pursuit = safe_float(
        extract_nested_value(data, 'seed', 'factors', 'pursuit'),
      )
      seed_sprint = safe_float(
        extract_nested_value(data, 'seed', 'factors', 'sprint'),
      )
      seed_punch = safe_float(
        extract_nested_value(data, 'seed', 'factors', 'punch'),
      )
      seed_climb = safe_float(
        extract_nested_value(data, 'seed', 'factors', 'climb'),
      )
      seed_time_trial_factor = safe_float(
        extract_nested_value(data, 'seed', 'factors', 'timeTrial'),
      )

      # Velo (vELO2)
      velo_race = safe_float(extract_nested_value(data, 'velo', 'race'))
      velo_time_trial = safe_float(
        extract_nested_value(data, 'velo', 'timeTrial'),
      )
      velo_endurance = safe_float(
        extract_nested_value(data, 'velo', 'factors', 'endurance'),
      )
      velo_pursuit = safe_float(
        extract_nested_value(data, 'velo', 'factors', 'pursuit'),
      )
      velo_sprint = safe_float(
        extract_nested_value(data, 'velo', 'factors', 'sprint'),
      )
      velo_punch = safe_float(
        extract_nested_value(data, 'velo', 'factors', 'punch'),
      )
      velo_climb = safe_float(
        extract_nested_value(data, 'velo', 'factors', 'climb'),
      )
      velo_time_trial_factor = safe_float(
        extract_nested_value(data, 'velo', 'factors', 'timeTrial'),
      )

      # Classify remaining fields
      excluded = {}
      extra = {}
      for key, value in data.items():
        if key not in known_fields:
          if key in recognized_but_excluded:
            excluded[key] = value
          else:
            extra[key] = value

      return cls(
        zwift_id=zwift_id,
        name=name,
        gender=gender,
        current_rating=current_rating,
        current_rank=current_rank,
        max30_rating=max30_rating,
        max30_rank=max30_rank,
        max90_rating=max90_rating,
        max90_rank=max90_rank,
        zrcs=zrcs,
        race_finishes=race_finishes,
        race_dnfs=race_dnfs,
        race_wins=race_wins,
        race_podiums=race_podiums,
        handicap_flat=handicap_flat,
        handicap_rolling=handicap_rolling,
        handicap_hilly=handicap_hilly,
        handicap_mountainous=handicap_mountainous,
        phenotype=phenotype_value,
        phenotype_bias=phenotype_bias,
        phenotype_sprinter=phenotype_sprinter,
        phenotype_puncheur=phenotype_puncheur,
        phenotype_pursuiter=phenotype_pursuiter,
        phenotype_climber=phenotype_climber,
        phenotype_tt=phenotype_tt,
        seed_race=seed_race,
        seed_time_trial=seed_time_trial,
        seed_endurance=seed_endurance,
        seed_pursuit=seed_pursuit,
        seed_sprint=seed_sprint,
        seed_punch=seed_punch,
        seed_climb=seed_climb,
        seed_time_trial_factor=seed_time_trial_factor,
        velo_race=velo_race,
        velo_time_trial=velo_time_trial,
        velo_endurance=velo_endurance,
        velo_pursuit=velo_pursuit,
        velo_sprint=velo_sprint,
        velo_punch=velo_punch,
        velo_climb=velo_climb,
        velo_time_trial_factor=velo_time_trial_factor,
        _excluded=excluded,
        _extra=extra,
      )

    except (KeyError, TypeError, ValueError) as e:
      logger.error(f'Error parsing rider rating data: {e}')
      return cls()

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with all public attributes
    """
    result = asdict(self)
    result.pop('_extra', None)
    result.pop('_excluded', None)
    return result

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields recognized but not explicitly handled.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields captured from API response.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)
