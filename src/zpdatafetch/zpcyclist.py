"""Python object representation for ZwiftPower cyclist profile data.

This module defines a typed Python object for cyclist profile data from
ZwiftPower's profile API endpoint. Wraps profile data and provides access
to the cyclist's race log via ZPRacelog.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from zpdatafetch.zpracelog import ZPRacelog


# ==============================================================================
@dataclass(slots=True)
class ZPCyclist:
  """Represents a cyclist's profile and race history from ZwiftPower.

  Provides attribute-based access to profile fields from ZwiftPower's profile
  API. The profile includes demographics, performance metrics, and race history.

  The race history is accessible via the `racelog` property, which returns a
  ZPRacelog object containing ZPRaceFinish objects for each race.

  Key cyclist information is extracted from the most recent race entry in the
  data array and exposed as direct attributes (team_id, team_name, gender,
  category, category_women, zftp, height, weight, skill, age).

  Attributes:
    zwift_id: Zwift ID from last race
    name: Rider name from last race
    team_id: Team ID from last race
    team_name: Team name from last race
    gender: Gender ("male" or "female")
    category: Men's category (A+/A/B/C/D)
    category_women: Women's category (A+/A/B/C/D)
    zftp: FTP from last race
    height: Height in cm
    weight: Weight in kg
    skill: Skill rating
    age: Age
    _data: Original API response dictionary (for backwards compatibility)
    _excluded: Recognized but not yet explicit fields
    _extra: Truly unknown fields from API
    _racelog: Cached ZPRacelog instance (lazy-loaded)

  Example:
    cyclist = ZPCyclist.from_dict({'zwid': 123, 'name': 'John', 'data': [...]})
    print(cyclist.team_name)  # 'Team XYZ'
    print(cyclist.gender)  # 'male'
    print(cyclist.category)  # 'B'
    racelog = cyclist.racelog  # Get ZPRacelog object
    for race in racelog:
      print(race.position)
  """

  # Key cyclist information (extracted from last race entry)
  zwift_id: int = 0  # Zwift ID
  name: str = ''  # Rider name
  team_id: int | None = None
  team_name: str | None = None
  gender: str = ''  # "male" or "female"
  category: str = ''  # Men's category (A+/A/B/C/D)
  category_women: str = ''  # Women's category (A+/A/B/C/D)
  zftp: int = 0  # FTP
  height: int = 0  # Height in cm
  weight: float = 0.0  # Weight in kg
  skill: float = 0.0  # Skill rating
  age: str = ''  # Age

  # Original API data (for backwards compatibility and raw access)
  _data: dict[str, Any] = field(default_factory=dict, repr=False)

  # Recognized but not yet explicit fields
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Truly unknown fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  # Cached racelog (not in repr)
  _racelog: ZPRacelog | None = field(default=None, repr=False, init=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPCyclist':
    """Create a ZPCyclist from API response dictionary.

    Separates known fields, recognized-but-unhandled fields, and truly unknown
    fields for proper classification. Extracts key cyclist information from the
    most recent (last) race entry in the data array.

    Args:
      data: Dictionary containing cyclist profile data from API

    Returns:
      New ZPCyclist instance with properly classified fields
    """
    from zpdatafetch.zp_utils import (
      convert_gender,
      set_rider_category,
    )

    # Fields we plan to eventually promote to explicit typed attributes
    # These are documented in the API but not yet handled natively
    recognized_but_excluded = {
      'zwid',  # Will become zwift_id
      'name',  # Will become name field
      'data',  # Will become race data
    }

    excluded = {}
    extra = {}

    for key, value in data.items():
      if key not in recognized_but_excluded:
        # For now, all other fields go to extra since cyclist is mostly a wrapper
        extra[key] = value

    # Extract key information from the last race entry
    zwift_id: int = 0
    name: str = ''
    team_id: int | None = None
    team_name: str | None = None
    gender: str = ''
    category: str = ''
    category_women: str = ''
    zftp: int = 0
    height: int = 0
    weight: float = 0.0
    skill: float = 0.0
    age: str = ''

    # Check if data array exists and has entries
    if 'data' in data and isinstance(data['data'], list) and data['data']:
      # Get the last (most recent) race entry
      last_race = data['data'][-1]

      # Extract zwift_id (could be 'zwid' or 'zid')
      zwid_raw = last_race.get('zwid') or last_race.get('zid')
      if zwid_raw is not None:
        try:
          zwift_id = int(zwid_raw)
        except (ValueError, TypeError):
          zwift_id = 0

      # Extract name
      name = str(last_race.get('name', ''))

      # Helper to extract value from array if needed
      def extract_value(value: Any) -> Any:
        """Extract first element from array if applicable."""
        if isinstance(value, list) and len(value) > 0:
          return value[0]
        return value

      # Extract team_id
      tid_raw = last_race.get('tid')
      if tid_raw is not None and tid_raw != '':
        try:
          team_id = int(tid_raw)
          if team_id == 0:
            team_id = None
        except (ValueError, TypeError):
          team_id = None

      # Extract team_name
      tname = last_race.get('tname')
      if tname:
        team_name = str(tname)

      # Extract and convert gender
      male_value = extract_value(last_race.get('male'))
      if male_value is not None:
        try:
          gender = convert_gender(int(male_value))
        except (ValueError, TypeError):
          gender = ''

      # Extract and convert categories
      div_value = extract_value(last_race.get('div', 0))
      try:
        category = set_rider_category(int(div_value) if div_value else 0)
      except (ValueError, TypeError):
        category = ''

      divw_value = extract_value(last_race.get('divw', 0))
      try:
        category_women = set_rider_category(
          int(divw_value) if divw_value else 0
        )
      except (ValueError, TypeError):
        category_women = ''

      # Extract FTP
      ftp_value = extract_value(last_race.get('ftp', 0))
      try:
        zftp = int(ftp_value) if ftp_value else 0
      except (ValueError, TypeError):
        zftp = 0

      # Extract height
      height_value = extract_value(last_race.get('height', 0))
      try:
        height = int(height_value) if height_value else 0
      except (ValueError, TypeError):
        height = 0

      # Extract weight
      weight_value = extract_value(last_race.get('weight', 0.0))
      try:
        weight = float(weight_value) if weight_value else 0.0
      except (ValueError, TypeError):
        weight = 0.0

      # Extract skill
      skill_value = extract_value(last_race.get('skill', 0.0))
      try:
        skill = float(skill_value) if skill_value else 0.0
      except (ValueError, TypeError):
        skill = 0.0

      # Extract age
      age_value = last_race.get('age', '')
      age = str(age_value) if age_value else ''

    return cls(
      zwift_id=zwift_id,
      name=name,
      team_id=team_id,
      team_name=team_name,
      gender=gender,
      category=category,
      category_women=category_women,
      zftp=zftp,
      height=height,
      weight=weight,
      skill=skill,
      age=age,
      _data=data,
      _excluded=excluded,
      _extra=extra,
    )

  def __getitem__(self, key: str) -> Any:
    """Allow dict-style access for backwards compatibility.

    Args:
      key: Field name to access

    Returns:
      Field value from cyclist data
    """
    return self._data[key]

  def __contains__(self, key: str) -> bool:
    """Check if field exists in cyclist data.

    Args:
      key: Field name to check

    Returns:
      True if field exists, False otherwise
    """
    return key in self._data

  def __repr__(self) -> str:
    """Return representation showing key cyclist information.

    Returns:
      String representation showing all extracted fields
    """
    parts = []

    # Add all key fields if available
    if self.zwift_id:
      parts.append(f'zwift_id={self.zwift_id}')
    if self.name:
      parts.append(f'name={self.name!r}')
    if self.team_id is not None:
      parts.append(f'team_id={self.team_id}')
    if self.team_name:
      parts.append(f'team_name={self.team_name!r}')
    if self.gender:
      parts.append(f'gender={self.gender!r}')
    if self.category:
      parts.append(f'category={self.category!r}')
    if self.category_women:
      parts.append(f'category_women={self.category_women!r}')
    if self.zftp:
      parts.append(f'zftp={self.zftp}')
    if self.height:
      parts.append(f'height={self.height}')
    if self.weight:
      parts.append(f'weight={self.weight}')
    if self.skill:
      parts.append(f'skill={self.skill}')
    if self.age:
      parts.append(f'age={self.age!r}')

    # If we have any parts, return formatted string
    if parts:
      return f'ZPCyclist({", ".join(parts)})'

    return 'ZPCyclist()'

  @property
  def racelog(self) -> ZPRacelog:
    """Get the cyclist's race history as a ZPRacelog object.

    Lazy-loads the racelog from the 'data' array on first access.

    Returns:
      ZPRacelog object containing ZPRaceFinish objects for each race

    Raises:
      KeyError: If 'data' field is missing from profile

    Example:
      cyclist = ZPCyclist.from_dict({'data': [...]})
      racelog = cyclist.racelog
      for race in racelog:
        print(f"Position {race.position}")
    """
    if self._racelog is None:
      if 'data' not in self._data:
        raise KeyError(
          'Cyclist profile missing "data" field. Cannot create racelog.',
        )
      self._racelog = ZPRacelog.from_dict(self._data['data'])
    return self._racelog

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields.

    These are fields documented in the API but not yet promoted to
    explicit typed attributes in the dataclass.

    Returns:
      Dictionary of recognized but unhandled fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown fields from API response.

    These fields are not yet recognized by the application,
    likely from recent API changes.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return original dictionary representation.

    Provides backwards compatibility with code expecting raw dicts.

    Returns:
      Original cyclist profile dictionary
    """
    return self._data

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of cyclist profile data
    """
    return json.dumps(self._data, indent=2)
