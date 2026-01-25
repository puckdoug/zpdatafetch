"""Represents league standings data from Zwiftpower."""

import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any, overload

from zpdatafetch.zp_utils import extract_numeric


@dataclass(slots=True)
class ZPLeagueTeam:
  """Represents a team in league standings.

  Contains team metadata including colors used for display.
  """

  team_id: str = ''  # Team ID
  name: str = ''  # Team name (tname)
  color_background: str = ''  # Background color hex (tbc)
  color_border: str = ''  # Border color hex (tbd)
  color_text: str = ''  # Text color hex (tc)

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, team_id: str, data: dict[str, Any]) -> 'ZPLeagueTeam':
    """Create instance from API response dict.

    Args:
      team_id: Team ID (key from teams dict)
      data: Dictionary containing team data

    Returns:
      ZPLeagueTeam instance with parsed fields
    """
    known_fields = {
      'tname',
      'tbc',
      'tbd',
      'tc',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    # (Currently none known for teams - all fields are handled)
    recognized_but_excluded: set[str] = set()

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
      team_id=team_id,
      name=str(data.get('tname', '')),
      color_background=str(data.get('tbc', '')),
      color_border=str(data.get('tbd', '')),
      color_text=str(data.get('tc', '')),
      _excluded=excluded,
      _extra=extra,
    )

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown/new fields from API response."""
    return dict(self._extra)

  def asdict(self) -> dict[str, Any]:
    """Return team data as dictionary with typed field values."""
    return {
      'team_id': self.team_id,
      'name': self.name,
      'color_background': self.color_background,
      'color_border': self.color_border,
      'color_text': self.color_text,
    }


@dataclass(slots=True)
class ZPLeagueResult:
  """Represents a rider's result in league standings.

  Contains rider position, points, category, and history.
  """

  # Core identification
  position: int = 0  # Position in standings
  zwift_id: int = 0  # Zwift user ID (zwid)
  aid: int = 0  # Alternative ID
  name: str = ''  # Rider name

  # League metrics
  points: int = 0  # League points total
  events: int = 0  # Number of events participated
  category: str = ''  # Category (A, B, C, D)

  # Team and location
  team_id: int = 0  # Team ID (tid)
  team_name: str = ''  # Team name (resolved from teams mapping)
  age: str = ''  # Age group (e.g., "60+", "Vet")
  flag: str = ''  # Country flag code

  # Performance history
  history: list[str] = field(
    default_factory=list, repr=False
  )  # List of past positions

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(
    cls,
    data: dict[str, Any],
    teams: dict[str, ZPLeagueTeam] | None = None,
  ) -> 'ZPLeagueResult':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing rider result data
      teams: Optional mapping of team ID to ZPLeagueTeam for resolving team names

    Returns:
      ZPLeagueResult instance with parsed fields
    """
    known_fields = {
      'pos',
      'zwid',
      'aid',
      'name',
      'points',
      'events',
      'category',
      'tid',
      'age',
      'flag',
      'history',
      # Also track aliases
      'position',
      'zwift_id',
      'team_id',
      'team_name',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'rank',
      'skill',
      'div',
      'divw',
    }

    # Extract history
    history = data.get('history', [])
    if not isinstance(history, list):
      history = []

    # Extract team_id and resolve team_name
    team_id = extract_numeric(data.get('tid'), int, 0)
    team_name = ''
    if teams and team_id > 0:
      team_id_str = str(team_id)
      if team_id_str in teams:
        team_name = teams[team_id_str].name

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
      position=extract_numeric(data.get('pos'), int, 0),
      zwift_id=extract_numeric(data.get('zwid'), int, 0),
      aid=extract_numeric(data.get('aid'), int, 0),
      name=str(data.get('name', '')),
      points=extract_numeric(data.get('points'), int, 0),
      events=extract_numeric(data.get('events'), int, 0),
      category=str(data.get('category', '')),
      team_id=team_id,
      team_name=team_name,
      age=str(data.get('age', '')),
      flag=str(data.get('flag', '')),
      history=history,
      _excluded=excluded,
      _extra=extra,
    )

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown/new fields from API response."""
    return dict(self._extra)

  def __getitem__(self, key: str) -> Any:
    """Allow dictionary-style access to rider data.

    Provides backwards compatibility with old dict-wrapper pattern.

    Args:
      key: Field name

    Returns:
      Value of the field
    """
    # Map API field names to attributes
    mapping = {
      'pos': 'position',
      'zwid': 'zwift_id',
      'aid': 'aid',
      'name': 'name',
      'points': 'points',
      'events': 'events',
      'category': 'category',
      'tid': 'team_id',
      'age': 'age',
      'flag': 'flag',
      'history': 'history',
      # Also support direct attribute names
      'position': 'position',
      'zwift_id': 'zwift_id',
      'team_id': 'team_id',
      'team_name': 'team_name',
    }
    if key in mapping:
      attr = mapping[key]
      return getattr(self, attr)
    raise KeyError(key)

  def asdict(self) -> dict[str, Any]:
    """Return rider data as dictionary with typed field values."""
    return {
      'position': self.position,
      'zwift_id': self.zwift_id,
      'aid': self.aid,
      'name': self.name,
      'points': self.points,
      'events': self.events,
      'category': self.category,
      'team_id': self.team_id,
      'team_name': self.team_name,
      'age': self.age,
      'flag': self.flag,
      'history': self.history,
    }


@dataclass(slots=True)
class ZPLeague(Sequence):
  """Represents league standings data.

  Contains teams and rider standings in a league, implementing Sequence protocol
  to provide array-like access to standings.

  Uses explicit typed fields for known API data with _excluded and _extra dicts
  to capture unhandled and unexpected fields for forward compatibility.

  Supports both legacy dict-based initialization and new dataclass pattern
  for backwards compatibility.
  """

  # League metadata
  league_id: int = 0  # League ID (injected by fetcher)

  # Nested data structures
  _teams: dict[str, ZPLeagueTeam] = field(
    default_factory=dict,
    repr=False,
  )  # Team info by team ID
  _standings: list[ZPLeagueResult] = field(
    default_factory=list,
    repr=False,
  )  # Rider standings

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  def __init__(
    self,
    league_data: dict[str, Any] | None = None,
    *,
    league_id: int = 0,
    _teams: dict[str, ZPLeagueTeam] | None = None,
    _standings: list[ZPLeagueResult] | None = None,
    _excluded: dict[str, Any] | None = None,
    _extra: dict[str, Any] | None = None,
  ) -> None:
    """Initialize a ZPLeague.

    Supports two patterns for backwards compatibility:
    1. ZPLeague(dict) - legacy dict-wrapper pattern (calls from_dict internally)
    2. ZPLeague.from_dict(dict) - new dataclass pattern (via kwargs)

    Args:
      league_data: Dictionary of league data (legacy pattern)
      league_id: League ID (from from_dict)
      _teams: Teams dict (from from_dict)
      _standings: Standings list (from from_dict)
      _excluded: Excluded fields dict (from from_dict)
      _extra: Extra fields dict (from from_dict)
    """
    if league_data is not None:
      # Legacy pattern: ZPLeague(dict)
      temp = ZPLeague.from_dict(league_data, league_id=league_id)
      self.league_id = temp.league_id
      self._teams = temp._teams
      self._standings = temp._standings
      self._excluded = temp._excluded
      self._extra = temp._extra
    else:
      # New dataclass pattern: from_dict() or direct kwargs
      self.league_id = league_id
      self._teams = _teams or {}
      self._standings = _standings or []
      self._excluded = _excluded or {}
      self._extra = _extra or {}

  @classmethod
  def from_dict(cls, data: dict[str, Any], league_id: int = 0) -> 'ZPLeague':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing league standings data
      league_id: League ID (used if not in data)

    Returns:
      ZPLeague instance with parsed fields
    """
    known_fields = {
      'teams',
      'data',
      'league_id',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'status',
      'message',
      'league_name',
    }

    # Parse teams dict into ZPLeagueTeam objects
    teams_data = data.get('teams', {})
    teams = {}
    if isinstance(teams_data, dict):
      for team_id, team_info in teams_data.items():
        if isinstance(team_info, dict):
          teams[team_id] = ZPLeagueTeam.from_dict(team_id, team_info)

    # Parse standings list into ZPLeagueResult objects
    standings_data = data.get('data', [])
    standings = []
    if isinstance(standings_data, list):
      for result_info in standings_data:
        if isinstance(result_info, dict):
          standings.append(ZPLeagueResult.from_dict(result_info, teams=teams))

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
      league_id=league_id,
      _teams=teams,
      _standings=standings,
      _excluded=excluded,
      _extra=extra,
    )

  def excluded(self) -> dict[str, Any]:
    """Return recognized-but-not-explicit fields."""
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return truly unknown/new fields from API response."""
    return dict(self._extra)

  # Sequence protocol
  def __len__(self) -> int:
    """Return number of riders in standings."""
    return len(self._standings)

  @overload
  def __getitem__(self, index: int) -> ZPLeagueResult: ...

  @overload
  def __getitem__(self, index: slice) -> list[ZPLeagueResult]: ...

  @overload
  def __getitem__(self, index: str) -> Any: ...

  def __getitem__(
    self,
    index: int | slice | str,
  ) -> ZPLeagueResult | list[ZPLeagueResult] | Any:
    """Get rider(s) by position/slice or dict-style access.

    Supports both Sequence protocol (integer/slice access to standings)
    and dict-style access (for backwards compatibility).

    Args:
      index: Integer index, slice, or dict key string

    Returns:
      Single/list of ZPLeagueResult objects (int/slice) or dict value (str key)
    """
    # Dict-style access
    if isinstance(index, str):
      if index == 'data':
        return self._standings
      if index == 'teams':
        return {tid: team.asdict() for tid, team in self._teams.items()}
      if index == 'league_id':
        return self.league_id
      raise KeyError(index)
    # Sequence-style access
    return self._standings[index]

  def __iter__(self) -> Iterator[ZPLeagueResult]:
    """Iterate over standings."""
    return iter(self._standings)

  def teams(self) -> dict[str, ZPLeagueTeam]:
    """Return teams dictionary.

    Returns:
      Mapping of team ID to ZPLeagueTeam objects
    """
    return dict(self._teams)

  def standings(self) -> list[ZPLeagueResult]:
    """Return standings list.

    Returns:
      List of ZPLeagueResult objects
    """
    return list(self._standings)

  def asdict(self) -> dict[str, Any]:
    """Return the league data as a dictionary with typed field values.

    Returns:
      Dictionary containing league standings data with nested teams and standings.
      Empty if league has no teams or standings.
    """
    result: dict[str, Any] = {'league_id': self.league_id}
    if self._teams:
      result['teams'] = {
        tid: team.asdict() for tid, team in self._teams.items()
      }
    if self._standings:
      result['standings'] = [
        result_obj.asdict() for result_obj in self._standings
      ]
    return result

  def json(self) -> str:
    """Return JSON representation of league data.

    Returns:
      JSON string with 2-space indentation
    """
    return json.dumps(self.asdict(), indent=2)
