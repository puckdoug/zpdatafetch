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
  position: int =0 # Position in standings
  zwift_id: int =0 # Zwift user ID (zwid)
  aid: int =0 # Alternative ID
  name: str = ''  # Rider name

  # League metrics
  points: int =0 # League points total
  events: int =0 # Number of events participated
  category: str = ''  # Category (A, B, C, D)

  # Team and location
  team_id: int =0 # Team ID (tid)
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
class ZPLeagueEvent:
  """Represents a race event in a league's calendar.

  Contains the event id, title, and start timefrom the league_event_results
  API. Uses explicit typed fields for known API data with _excluded and _extra
  dicts to capture unhandled and unexpected fields for forward compatibility.
  """

  # Core identification
  event_id: int =0 # Event ID (zid/DT_RowId)
  title: str = ''  # Event title (t)

  # Event timing
  start_datetime: int =0 # Start time (tm), Unix epoch seconds

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)



  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPLeagueEvent':
    """Create instance from API response dict.



    Args:
      data: Dictionary containing event data



    Returns:
      ZPLeagueEvent instance with parsed fields
    """
    known_fields = {
      'zid',
      't',
      'tm',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'DT_RowId',  # Duplicate of zid (DataTables row id)
      'results',  # Per-category result rows; not typed in this change
    }

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
      event_id=extract_numeric(data.get('zid'), int, 0),
      title=str(data.get('t', '')),
      start_datetime=extract_numeric(data.get('tm'), int, 0),
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
    """Return event data as dictionary with typed field values."""
    return {
      'event_id': self.event_id,
      'title': self.title,
      'start_datetime': self.start_datetime,
    }


@dataclass(slots=True)
class ZPLeagueTeamStanding:
  """Represents a team's standing in a league's team standings.

    Contains team position, points, event count, history, colors, and rank.
  """

  # Core identification
  team_id: int =0 # Team ID (tid)
  team_name: str = ''  # Team name (tname)

  # Standings metrics
  position: int =0 # Position in team standings (pos)
  points: int =0 # Total team points
  events: int =0 # Events participated
  rank: str = ''  # Rank fraction (e.g. "100.00%")
  history: list[str] = field(default_factory=list, repr=False)  # Past positions

  # Category
  category: str = ''  # Category (A, B, C, D)

  # Display colors
  color_background: str = ''  # Background color hex (tbc)
  color_border: str = ''  # Border color hex (tbd)
  color_text: str = ''  # Text color hex (tc)

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)



  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)



  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPLeagueTeamStanding':
    """Create instance from API response dict.



    Args:
      data: Dictionary containing team standing data



    Returns:
      ZPLeagueTeamStanding instance with parsed fields
    """
    known_fields = {
      'tid',
      'tname',
      'pos',
      'points',
      'events',
      'rank',
      'history',
      'category',
      'tbc',
      'tbd',
      'tc',
    }

    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'league_id',   # Duplicate of league id
    }

    # Extract history
    history = data.get('history', [])
    if not isinstance(history, list):
      history = []

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
      team_id=extract_numeric(data.get('tid'), int, 0),
      team_name=str(data.get('tname', '')),
      position=extract_numeric(data.get('pos'), int, 0),
      points=extract_numeric(data.get('points'), int, 0),
      events=extract_numeric(data.get('events'), int, 0),
      rank=str(data.get('rank', '')),
      history=history,
      category=str(data.get('category', '')),
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
    """Return team standing data as dictionary with typed field values."""
    return {
      'team_id': self.team_id,
      'team_name': self.team_name,
      'position': self.position,
      'points': self.points,
      'events': self.events,
      'rank': self.rank,
      'history': self.history,
      'category': self.category,
      'color_background': self.color_background,
      'color_border': self.color_border,
      'color_text': self.color_text,
    }


@dataclass(slots=True)
class ZPLeagueTeamEventResult:
  """Represents a rider's row in a league's team-event standings.

  Contains rider position, category, team, points, and rank from the
  league_team_event_standings API for one event view.
  """

  # Core identification
  zwift_id: int =0 # Zwift user ID (zwid)
  name: str = ''  # Rider name
  category: str = ''  # Category (A, B, C, D)

  # Team
  team_id: int =0 # Team ID (tid)
  team_name: str = ''  # Team name (tname)
  color_background: str = ''  # Background color hex (tbc)
  color_border: str = ''  # Border color hex (tbd)
  color_text: str = ''  # Text color hex (tc)

  # Standings metrics
  position: int =0 # Position (pos)
  points: int =0 # Points
  events: int =0 # Events participated
  rank: str = ''  # Rank fraction (e.g. "100.00%")
  reg: int =0 # Region ID (reg)
  flag: str = ''  # Country flag code

  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)



  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)



  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPLeagueTeamEventResult':
    """Create instance from API response dict.



    Args:
      data: Dictionary containing team-event standing data



    Returns:
      ZPLeagueTeamEventResult instance with parsed fields
    """
    known_fields = {
      'zwid',
      'name',
      'category',
      'tid',
      'tname',
      'tbc',
      'tbd',
      'tc',
      'pos',
      'points',
      'events',
      'rank',
      'reg',
      'flag',
    }



    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'topen',
      'fem',
    }



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
      zwift_id=extract_numeric(data.get('zwid'), int, 0),
      name=str(data.get('name', '')),
      category=str(data.get('category', '')),
      team_id=extract_numeric(data.get('tid'), int, 0),
      team_name=str(data.get('tname', '')),
      color_background=str(data.get('tbc', '')),
      color_border=str(data.get('tbd', '')),
      color_text=str(data.get('tc', '')),
      position=extract_numeric(data.get('pos'), int, 0),
      points=extract_numeric(data.get('points'), int, 0),
      events=extract_numeric(data.get('events'), int, 0),
      rank=str(data.get('rank', '')),
      reg=extract_numeric(data.get('reg'), int, 0),
      flag=str(data.get('flag', '')),
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
    """Return rider row as dictionary with typed field values."""
    return {
      'zwift_id': self.zwift_id,
      'name': self.name,
      'category': self.category,
      'team_id': self.team_id,
      'team_name': self.team_name,
      'color_background': self.color_background,
      'color_border': self.color_border,
      'color_text': self.color_text,
      'position': self.position,
      'points': self.points,
      'events': self.events,
      'rank': self.rank,
      'reg': self.reg,
      'flag': self.flag,
    }


@dataclass(slots=True)
class ZPLeagueInfo:
  """Represents a league's metadata from the league catalog API.


  Contains league name, contact, info, categories, active status, counts,
  and display colors from a league_list row.
  """


  # Core identification
  league_id: int =0 # League ID
  name: str = ''  # League name (league_name)


  # League description
  active: int =0 # Active flag (0/1)


  info: str = ''  # League info/description
  contact: str = ''  # Contact email/string


  # Schedule
  start: int =0 # Start week/round (start)
  end: int =0 # End week/round (end)
  categories: str = ''  # Category letters (cats)
  category_names: str = ''  # Category display names (cats_names)


  # Activity counts
  races: int =0 # Race count (races)
  efforts: int =0 # Effort count (efforts)


  # Display info
  image: str = ''  # Image ID/path
  color_background: str = ''  # Background color hex (lidbc)
  color_border: str = ''  # Border color hex (lidbd)
  color_text: str = ''  # Text color hex (lidc)
  latest_race_id: str = ''  # Latest league race id (lrace_id)
  race_id: str = ''  # Open race id (race_id, maybe empty)
  latest_race_title: str = ''  # Latest league race title (lrace_title)


  # Excluded fields - recognized but not explicitly handled
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)



  # Catch-all for unknown/new fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)



  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZPLeagueInfo':
    """Create instance from API response dict.



    Args:
      data: Dictionary containing a league_list row



    Returns:
      ZPLeagueInfo instance with parsed fields
    """
    known_fields = {
      'league_id',
      'league_name',
      'active',
      'info',
      'contact',
      'start',
      'end',
      'cats',
      'cats_names',
      'races',
      'efforts',
      'image',
      'lidbc',
      'lidbd',
      'lidc',
      'lrace_id',
      'race_id',
      'lrace_title',
    }



    # Fields recognized from API but not explicitly handled as typed fields
    recognized_but_excluded = {
      'ridc',
      'ridbd',
      'ridbc',
    }



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
      league_id=extract_numeric(data.get('league_id'), int, 0),
      name=str(data.get('league_name', '')),
      active=extract_numeric(data.get('active'), int, 0),
      info=str(data.get('info', '')),
      contact=str(data.get('contact', '')),
      start=extract_numeric(data.get('start'), int, 0),
      end=extract_numeric(data.get('end'), int, 0),
      categories=str(data.get('cats', '')),
      category_names=str(data.get('cats_names', '')),
      races=extract_numeric(data.get('races'), int, 0),
      efforts=extract_numeric(data.get('efforts'), int, 0),
      image=str(data.get('image', '')),
      color_background=str(data.get('lidbc', '')),
      color_border=str(data.get('lidbd', '')),
      color_text=str(data.get('lidc', '')),
      latest_race_id=str(data.get('lrace_id', '')),
      race_id=str(data.get('race_id', '')),
      latest_race_title=str(data.get('lrace_title', '')),
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
    """Return league info as dictionary with typed field values."""
    return {
      'league_id': self.league_id,
      'name': self.name,
      'active': self.active,
      'info': self.info,
      'contact': self.contact,
      'start': self.start,
      'end': self.end,
      'categories': self.categories,
      'category_names': self.category_names,
      'races': self.races,
      'efforts': self.efforts,
      'image': self.image,
      'color_background': self.color_background,
      'color_border': self.color_border,
      'color_text': self.color_text,
      'latest_race_id': self.latest_race_id,
      'race_id': self.race_id,
      'latest_race_title': self.latest_race_title,
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
  league_id: int =0 # League ID (injected by fetcher)

  # Nested data structures
  _teams: dict[str, ZPLeagueTeam] = field(
    default_factory=dict,
    repr=False,
  )  # Team info by team ID
  _standings: list[ZPLeagueResult] = field(
    default_factory=list,
    repr=False,
  )  # Rider standings
  _team_standings: list[ZPLeagueTeamStanding] = field(
    default_factory=list,
    repr=False,
  )  # Team standings rows
  _team_event_results: list[ZPLeagueTeamEventResult] = field(
    default_factory=list,
    repr=False,
  )  # Team-event standings rows
  _events: list[ZPLeagueEvent] = field(
    default_factory=list,
    repr=False,
  )  # League events
  _info: ZPLeagueInfo | None = field(default=None, repr=False)  # League catalog metadata

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
    _team_standings: list[ZPLeagueTeamStanding] | None = None,
    _team_event_results: list[ZPLeagueTeamEventResult] | None = None,
    _events: list[ZPLeagueEvent] | None = None,
    _info: ZPLeagueInfo | None = None,
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
      _team_standings: Team standings list (from from_dict)
      _team_event_results: Team-event standings list (from from_dict)
      _events: Events list (from from_dict)
      _info: League catalog metadata (from from_dict)
      _excluded: Excluded fields dict (from from_dict)
      _extra: Extra fields dict (from from_dict)
    """
    if league_data is not None:
      # Legacy pattern: ZPLeague(dict)
      temp = ZPLeague.from_dict(league_data, league_id=league_id)
      self.league_id = temp.league_id
      self._teams = temp._teams
      self._standings = temp._standings
      self._team_standings = temp._team_standings
      self._team_event_results = temp._team_event_results
      self._events = temp._events
      self._info = temp._info
      self._excluded = temp._excluded
      self._extra = temp._extra
    else:
      # New dataclass pattern: from_dict() or direct kwargs
      self.league_id = league_id
      self._teams = _teams or {}
      self._standings = _standings or []
      self._team_standings = _team_standings or []
      self._team_event_results = _team_event_results or []
      self._events = _events or []
      self._info = _info
      self._excluded = _excluded or {}
      self._extra = _extra or {}

  @classmethod
  def from_dict(
    cls,
    data: dict[str, Any],
    league_id: int = 0,
    *,
    events: list[dict[str, Any]] | None = None,
    team_standings: list[dict[str, Any]] | None = None,
    team_event_results: list[dict[str, Any]] | None = None,
    league_info: dict[str, Any] | ZPLeagueInfo | None = None,
  ) -> 'ZPLeague':
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

    # Parse league events
    events_parsed: list[ZPLeagueEvent] = []
    if isinstance(events, list):
      for e in events:
        if isinstance(e, dict):
          events_parsed.append(ZPLeagueEvent.from_dict(e))

    # Parse team standings
    team_standings_parsed: list[ZPLeagueTeamStanding] = []
    if isinstance(team_standings, list):
      for r in team_standings:
        if isinstance(r, dict):
          team_standings_parsed.append(ZPLeagueTeamStanding.from_dict(r))

    # Parse team-event standings
    team_event_results_parsed: list[ZPLeagueTeamEventResult] = []
    if isinstance(team_event_results, list):
      for r in team_event_results:
        if isinstance(r, dict):
          team_event_results_parsed.append(ZPLeagueTeamEventResult.from_dict(r))
    # Parse league info (dict or already-built object)
    info_parsed = None
    if isinstance(league_info, ZPLeagueInfo):
      info_parsed = league_info
    elif isinstance(league_info, dict):
      info_parsed = ZPLeagueInfo.from_dict(league_info)

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
      _team_standings=team_standings_parsed,
      _team_event_results=team_event_results_parsed,
      _events=events_parsed,
      _info=info_parsed,
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
      if index == 'team_standings':
        return self._team_standings
      if index == 'team_event_results':
        return self._team_event_results
      if index == 'events':
        return self._events
      if index == 'league_info':
        return self._info
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

  def team_standings(self) -> list[ZPLeagueTeamStanding]:
    """Return team standings rows.

    Returns:
      List of ZPLeagueTeamStanding objects
    """
    return list(self._team_standings)

  def team_event_results(self) -> list[ZPLeagueTeamEventResult]:
    """Return team-event standings rows.

    Returns:
      List of ZPLeagueTeamEventResult objects
    """
    return list(self._team_event_results)

  def events(self) -> list[ZPLeagueEvent]:
    """Return league events.

    Returns:
      List of ZPLeagueEvent objects
    """
    return list(self._events)

  def info(self) -> ZPLeagueInfo | None:
    """Return league catalog metadata."""
    return self._info

  def asdict(self) -> dict[str, Any]:
    """Return the league data as a dictionary with typed field values.

    Returns:
      Dictionary containing league data with nested league info, teams,
      standings, team standings, team-event results, and events.
    """
    result: dict[str, Any] = {'league_id': self.league_id}
    if self._info:
      result['league_info'] = self._info.asdict()
    if self._teams:
      result['teams'] = {
        tid: team.asdict() for tid, team in self._teams.items()
      }
    if self._standings:
      result['standings'] = [
        result_obj.asdict() for result_obj in self._standings
      ]
    if self._team_standings:
      result['team_standings'] = [
        row.asdict() for row in self._team_standings
      ]
    if self._team_event_results:
      result['team_event_results'] = [
        row.asdict() for row in self._team_event_results
      ]
    if self._events:
      result['events'] = [
        event.asdict() for event in self._events
      ]
    return result

  def json(self) -> str:
    """Return JSON representation of league data.

    Returns:
      JSON string with 2-space indentation
    """
    return json.dumps(self.asdict(), indent=2)
