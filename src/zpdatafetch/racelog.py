"""Collection of race finishes for a cyclist."""

from collections.abc import Iterator
from typing import Any

from zpdatafetch.race_finish import RaceFinish


class Racelog:
  """Collection of race finishes supporting array-like operations.

  Wraps a list of RaceFinish objects and provides array-like access
  including indexing, iteration, and len().

  Example:
    racelog = Racelog(race_data_list)
    print(len(racelog))  # Number of races
    first_race = racelog[0]  # Get first race
    for race in racelog:  # Iterate over races
      print(race.event_title)
  """

  def __init__(self, race_data_list: list[dict[str, Any]]) -> None:
    """Initialize Racelog from list of race data dictionaries.

    Args:
      race_data_list: List of race data dictionaries
    """
    self._races = [RaceFinish(race_data) for race_data in race_data_list]

  def __len__(self) -> int:
    """Return the number of races.

    Returns:
      Number of RaceFinish objects
    """
    return len(self._races)

  def __getitem__(self, index: int | slice) -> RaceFinish | list[RaceFinish]:
    """Support indexing and slicing.

    Args:
      index: Integer index or slice

    Returns:
      Single RaceFinish or list of RaceFinish objects
    """
    return self._races[index]

  def __iter__(self) -> Iterator[RaceFinish]:
    """Support iteration over races.

    Returns:
      Iterator over RaceFinish objects
    """
    return iter(self._races)

  def __repr__(self) -> str:
    """Return string representation."""
    return f'Racelog({len(self._races)} races)'

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of race data dictionaries for JSON serialization.

    Returns:
      List of dictionaries containing race data
    """
    return [race.asdict() for race in self._races]
