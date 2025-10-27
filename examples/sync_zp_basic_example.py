#!/usr/bin/env python3
"""Basic example of using the synchronous zpdatafetch API.

This example demonstrates how to fetch Zwiftpower data synchronously,
which is suitable for simple scripts and applications that don't need
concurrent operations.

Note: You must be logged in to Zwiftpower to use this API. Authentication
credentials are handled automatically through your Zwiftpower session.
"""

from zpdatafetch import ZP, Cyclist, Result, Team


def main():
  """Fetch Zwiftpower data synchronously."""
  print('Zwiftpower Data Fetching Examples')
  print('=' * 60)

  # ============================================================================
  # Example 1: Login to Zwiftpower
  # ============================================================================
  print('\n1. Login to Zwiftpower')
  print('-' * 60)

  zp = ZP()
  print('Logging in to Zwiftpower...')

  # Note: Authentication happens automatically based on your credentials
  # If you're not authenticated, you may need to configure your credentials
  # See the configuration section of the README for details

  # ============================================================================
  # Example 2: Fetch a cyclist's profile
  # ============================================================================
  print("\n2. Fetch a cyclist's profile")
  print('-' * 60)

  cyclist = Cyclist()
  cyclist.set_session(zp)

  print('Fetching cyclist data for ID 123456...')
  cyclist_data = cyclist.fetch(123456)

  if cyclist_data:
    print(f'Cyclist Name: {cyclist.name}')
    print(f'Athlete ID: {cyclist.athlete_id}')
    print(f'Team: {cyclist.team}')
    if hasattr(cyclist, 'power_meter'):
      print(f'Power Meter: {cyclist.power_meter}')
  else:
    print('Could not fetch cyclist data')

  # ============================================================================
  # Example 3: Fetch race results
  # ============================================================================
  print('\n3. Fetch race results')
  print('-' * 60)

  result = Result()
  result.set_session(zp)

  print('Fetching race results for ID 3590800...')
  race_data = result.fetch(3590800)

  if race_data:
    print(f'Race ID: {result.race_id}')
    print(f'Name: {result.name}')
    print(f'Category: {result.category}')
    print(f'Event Type: {result.event_type}')
    if hasattr(result, 'number_of_laps'):
      print(f'Number of Laps: {result.number_of_laps}')
  else:
    print('Could not fetch race results')

  # ============================================================================
  # Example 4: Fetch team information
  # ============================================================================
  print('\n4. Fetch team information')
  print('-' * 60)

  team = Team()
  team.set_session(zp)

  print('Fetching team data for ID 456...')
  team_data = team.fetch(456)

  if team_data:
    print(f'Team Name: {team.name}')
    print(f'Team ID: {team.team_id}')
    print(f'Category: {team.category}')
    if hasattr(team, 'number_of_members'):
      print(f'Number of Members: {team.number_of_members}')
  else:
    print('Could not fetch team data')

  # ============================================================================
  # Example 5: Fetch race signups
  # ============================================================================
  print('\n5. Fetch race signups')
  print('-' * 60)

  from zpdatafetch import Signup

  signup = Signup()
  signup.set_session(zp)

  print('Fetching signup data for race ID 3590800...')
  signup_data = signup.fetch(3590800)

  if signup_data:
    print(f'Race ID: {signup.race_id}')
    if hasattr(signup, 'total_signups'):
      print(f'Total Signups: {signup.total_signups}')
    print(
      f'Number of signup entries: {len(signup_data) if isinstance(signup_data, list) else "N/A"}'
    )
  else:
    print('Could not fetch signup data')

  # ============================================================================
  # Example 6: Get full JSON representation
  # ============================================================================
  print('\n6. Full JSON representation of cyclist')
  print('-' * 60)

  cyclist_json = cyclist.json()
  print(f'Number of fields: {len(cyclist_json)}')
  print(f'Keys: {list(cyclist_json.keys())[:5]}...')

  print('\n' + '=' * 60)
  print('Zwiftpower examples completed!')


if __name__ == '__main__':
  main()
