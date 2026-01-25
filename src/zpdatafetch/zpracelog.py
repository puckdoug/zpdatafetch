"""Collection of race finishes for a cyclist."""

import json
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any, cast, overload

from zpdatafetch.zpracefinish import ZPRaceFinish


@dataclass(slots=True)
class ZPRacelog(Sequence):
  """Collection of race finishes supporting array-like operations.

  Wraps a list of ZPRaceFinish objects and provides array-like access
  including indexing, iteration, and len().

  Attributes:
    _races: List of ZPRaceFinish objects
    _excluded: Recognized but not yet explicit fields
    _extra: Truly unknown fields from API

  Example:
    # Recommended: use from_dict factory method
    racelog = ZPRacelog.from_dict(race_data_list)

    # Or create directly and add races
    racelog = ZPRacelog()

    # Access races
    print(len(racelog))  # Number of races
    first_race = racelog[0]  # Get first race
    for race in racelog:  # Iterate over races
      print(race.position)
  """

  # Internal list of races (not in repr)
  _races: list[ZPRaceFinish] = field(default_factory=list, repr=False)

  # Recognized but not yet explicit fields
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)

  # Truly unknown fields from API
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  def __post_init__(self) -> None:
    """Support backwards-compatibility: accept race data list in first positional arg.

    This allows both:
      ZPRacelog([...])  # Old style
      ZPRacelog.from_dict([...])  # New style
      ZPRacelog()  # Empty
    """
    # If _races was passed as a list of dicts instead of ZPRaceFinish objects,
    # convert them now for backwards compatibility
    if self._races and isinstance(self._races[0], dict):
      converted_races: list[ZPRaceFinish] = []
      for race_item in self._races:
        if isinstance(race_item, dict):
          race_dict = cast('dict[str, Any]', race_item)
          converted_races.append(ZPRaceFinish.from_dict(race_dict))
        else:
          # race_item is already a ZPRaceFinish
          converted_races.append(race_item)
      self._races = converted_races

  @classmethod
  def from_dict(
    cls, race_data_list: list[dict[str, Any]] | None
  ) -> 'ZPRacelog':
    """Create a ZPRacelog from list of race data dictionaries.

    Args:
      race_data_list: List of race data dictionaries.
                      If None, creates an empty racelog object.

    Returns:
      New ZPRacelog instance with races parsed into ZPRaceFinish objects
    """
    data_list = race_data_list if race_data_list is not None else []
    races = [ZPRaceFinish.from_dict(race_data) for race_data in data_list]

    return cls(
      _races=races,
      _excluded={},
      _extra={},
    )

  def __len__(self) -> int:
    """Return the number of races.

    Returns:
      Number of RaceFinish objects
    """
    return len(self._races)

  @overload
  def __getitem__(self, index: int) -> ZPRaceFinish: ...

  @overload
  def __getitem__(self, index: slice) -> list[ZPRaceFinish]: ...

  def __getitem__(
    self, index: int | slice
  ) -> ZPRaceFinish | list[ZPRaceFinish]:
    """Support indexing and slicing.

    Args:
      index: Integer index or slice

    Returns:
      Single ZPRaceFinish or list of ZPRaceFinish objects
    """
    return self._races[index]

  def __iter__(self) -> Iterator[ZPRaceFinish]:
    """Support iteration over races.

    Returns:
      Iterator over ZPRaceFinish objects
    """
    return iter(self._races)

  def __repr__(self) -> str:
    """Return representation showing all races.

    Returns:
      String in format: ZPRacelog([ ZPRaceFinish(...), ZPRaceFinish(...) ])
    """
    if len(self._races) == 0:
      return 'ZPRacelog([])'

    race_reprs = [repr(race) for race in self._races]
    return 'ZPRacelog([\n  ' + ',\n  '.join(race_reprs) + '\n])'

  def __str__(self) -> str:
    """Return human-readable string showing all races.

    Returns:
      String in format: ZPRacelog[ ZPRaceFinish(...), ZPRaceFinish(...) ]
    """
    if len(self._races) == 0:
      return 'ZPRacelog[]'

    race_reprs = [repr(race) for race in self._races]
    return 'ZPRacelog[\n  ' + ',\n  '.join(race_reprs) + '\n]'

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

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of race data dictionaries for JSON serialization.

    Returns:
      List of dictionaries containing race data
    """
    return [race.asdict() for race in self._races]

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation with typed field values.

    Returns:
      Dictionary with races list only
    """
    return {
      'races': self.aslist(),
    }

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of racelog data
    """
    return json.dumps(self.asdict(), indent=2)

  def days_last(self, days: int) -> 'ZPRacelog':
    """Return a new ZPRacelog containing only races from the last N days.

    Filters races based on event_date field (Unix epoch timestamp).
    Only includes races within the specified number of days from the current time.

    Args:
      days: Number of days to look back from current time

    Returns:
      New ZPRacelog object containing only races from last N days

    Example:
      racelog = cyclist.racelog
      last_30 = racelog.days_last(30)
      last_90 = racelog.days_last(90)
      print(f"Races in last 30 days: {len(last_30)}")
    """
    # Calculate cutoff timestamp (N days ago)
    days_in_seconds = days * 24 * 60 * 60
    cutoff_timestamp = time.time() - days_in_seconds

    # Filter races with event_date >= cutoff
    recent_races = []
    for race in self._races:
      # Access numeric timestamp for comparison (use _event_date_timestamp which is stored as float)
      event_date_timestamp = (
        race._event_date_timestamp
        if hasattr(race, '_event_date_timestamp')
        else 0
      )
      if event_date_timestamp >= cutoff_timestamp:
        recent_races.append(race)

    # Return new ZPRacelog with filtered races
    new_racelog = ZPRacelog(_races=recent_races)
    return new_racelog
