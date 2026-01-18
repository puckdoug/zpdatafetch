"""Python object representations for ZwiftPower team data.

This module defines typed Python objects for team roster data from ZwiftPower's
team API endpoint. Provides both collection and individual team member classes
with attribute access and backwards compatibility.
"""

from typing import Any


# ===============================================================================
class ZPTeamMember:
  """Represents a single team member in a team roster.

  Provides attribute-based access to team member fields from ZwiftPower's
  team API. Supports both attribute access (obj.field) and dict-style
  access (obj['field']) for backwards compatibility.

  Example:
    member = ZPTeamMember({'zwid': 123, 'name': 'John Doe'})
    print(member.name)  # 'John Doe'
    print(member['zwid'])  # 123
    data = member.asdict()  # Get original dict
  """

  def __init__(self, member_data: dict[str, Any]) -> None:
    """Initialize a team member.

    Args:
      member_data: Dictionary containing team member data from API
    """
    self._data = member_data

  def __getattr__(self, name: str) -> Any:
    """Allow attribute access to team member fields.

    Args:
      name: Field name to access

    Returns:
      Field value from member data

    Raises:
      AttributeError: If field doesn't exist
    """
    # Prevent infinite recursion for _data and other private attributes
    if name.startswith('_'):
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      )

    try:
      return self._data[name]
    except KeyError as e:
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      ) from e

  def __getitem__(self, key: str) -> Any:
    """Allow dict-style access for backwards compatibility.

    Args:
      key: Field name to access

    Returns:
      Field value from member data
    """
    return self._data[key]

  def __contains__(self, key: str) -> bool:
    """Check if field exists in member data.

    Args:
      key: Field name to check

    Returns:
      True if field exists, False otherwise
    """
    return key in self._data

  def asdict(self) -> dict[str, Any]:
    """Return original dictionary representation.

    Provides backwards compatibility with code expecting raw dicts.

    Returns:
      Original member data dictionary
    """
    return self._data

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of member data
    """
    import json

    return json.dumps(self._data, indent=2)


# ===============================================================================
class ZPTeam:
  """Collection of team members for a team roster.

  Provides array-like access to individual team members from ZwiftPower's
  team API. Supports iteration, indexing, and slicing.

  The team data includes team metadata and a list of team members.
  Each member is wrapped in a ZPTeamMember object for typed access.

  Example:
    team = ZPTeam({'data': [{'name': 'John'}, {'name': 'Jane'}]})
    print(len(team))  # 2
    print(team[0].name)  # 'John'
    for member in team:
      print(member.name)
  """

  def __init__(self, team_data: dict[str, Any]) -> None:
    """Initialize a team roster collection.

    Args:
      team_data: Dictionary containing team data from API,
                 including 'data' array of team members
    """
    self._data = team_data

    # Extract team member list
    member_list = team_data.get('data', [])

    # Create ZPTeamMember objects for each member
    self._members = [ZPTeamMember(member_data) for member_data in member_list]

  def __len__(self) -> int:
    """Return number of team members.

    Returns:
      Count of team members
    """
    return len(self._members)

  def __getitem__(self, index: int | slice) -> 'ZPTeamMember | list[ZPTeamMember]':
    """Access team members by index or slice.

    Args:
      index: Integer index or slice object

    Returns:
      Single ZPTeamMember or list of ZPTeamMember objects
    """
    return self._members[index]

  def __iter__(self):
    """Iterate over team members.

    Returns:
      Iterator over ZPTeamMember objects
    """
    return iter(self._members)

  def asdict(self) -> dict[str, Any]:
    """Return original dictionary representation.

    Provides backwards compatibility with code expecting raw dicts.

    Returns:
      Original team data dictionary
    """
    return self._data

  def aslist(self) -> list[dict[str, Any]]:
    """Return list of team member dictionaries.

    Useful for serialization or backwards compatibility.

    Returns:
      List of team member dictionaries
    """
    return [member.asdict() for member in self._members]

  def json(self) -> str:
    """Return JSON string representation.

    Returns:
      JSON-formatted string of team data
    """
    import json

    return json.dumps(self._data, indent=2)
