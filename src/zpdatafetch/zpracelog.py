"""Collection of race finishes for a cyclist."""

import time
from collections.abc import Iterator
from typing import Any

from zpdatafetch.zpracefinish import ZPRaceFinish


class ZPRacelog:
  """Collection of race finishes supporting array-like operations.

  Wraps a list of ZPRaceFinish objects and provides array-like access
  including indexing, iteration, and len().

  Example:
    racelog = ZPRacelog(race_data_list)
    print(len(racelog))  # Number of races
    first_race = racelog[0]  # Get first race
    for race in racelog:  # Iterate over races
      print(race.event_title)
  """

  def __init__(self, race_data_list: list[dict[str, Any]] | None = None) -> None:
    """Initialize ZPRacelog from list of race data dictionaries.

    Args:
      race_data_list: List of race data dictionaries.
                      If None, creates an empty racelog object.
    """
    data_list = race_data_list if race_data_list is not None else []
    self._races = [ZPRaceFinish(race_data) for race_data in data_list]

  def __len__(self) -> int:
    """Return the number of races.

    Returns:
      Number of RaceFinish objects
    """
    return len(self._races)

  def __getitem__(self, index: int | slice) -> ZPRaceFinish | list[ZPRaceFinish]:
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

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of race data dictionaries for JSON serialization.

    Returns:
      List of dictionaries containing race data
    """
    return [race.asdict() for race in self._races]

  def days_last(self, days: int) -> 'ZPRacelog':
    """Return a new ZPRacelog containing only races from the last N days.

    Filters races based on event_date field (Unix epoch timestamp).
    Only includes races within the specified number of days from the current time.

    Args:
      days: Number of days to look back from current time

    Returns:
      New ZPRacelog object containing only races from last N days

    Example:
      racelog = cyclist.racelog(7574336)
      last_30 = racelog.days_last(30)
      last_90 = racelog.days_last(90)
      print(f"Races in last 30 days: {len(last_30)}")
    """
    # Calculate cutoff timestamp (N days ago)
    days_in_seconds = days * 24 * 60 * 60
    cutoff_timestamp = time.time() - days_in_seconds

    # Filter races with event_date >= cutoff
    recent_race_data = []
    for race in self._races:
      event_date = race._data.get('event_date', 0)
      if event_date >= cutoff_timestamp:
        recent_race_data.append(race._data)

    # Return new ZPRacelog with filtered data
    return ZPRacelog(recent_race_data)
