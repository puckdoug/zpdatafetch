#!/usr/bin/env python3
"""Advanced example of using the synchronous zpdatafetch API.

This example demonstrates advanced features including:
- Fetching related data (races and their primes)
- Combining data from multiple sources
- Error handling and retries
- Working with optional fields
"""

from zpdatafetch import ZP, Cyclist, Primes, Result, Signup, Team


def fetch_race_with_details(race_id: int):
  """Fetch race details including results and primes."""
  print(f'\nFetching race {race_id} with details...')
  print('-' * 60)

  zp = ZP()

  try:
    # Fetch race results
    result = Result()
    result.set_session(zp)
    result.fetch(race_id)

    print(f'Race: {result.name}')
    print(f'Category: {result.category if hasattr(result, "category") else "N/A"}')
    print(f'Type: {result.event_type if hasattr(result, "event_type") else "N/A"}')

    # Fetch primes for the race
    primes = Primes()
    primes.set_session(zp)
    primes_data = primes.fetch(race_id)

    if primes_data:
      print('\nPrimes available: Yes')
      print(
        f'Number of primes: {len(primes_data) if isinstance(primes_data, list) else "Unknown"}'
      )
    else:
      print('\nPrimes available: No')

    # Fetch signups
    signup = Signup()
    signup.set_session(zp)
    signup_data = signup.fetch(race_id)

    if signup_data:
      print(
        f'Number of signups: {len(signup_data) if isinstance(signup_data, list) else "Unknown"}'
      )
    else:
      print('Signup data: Not available')

    return {
      'race_id': race_id,
      'name': result.name,
      'category': result.category if hasattr(result, 'category') else None,
      'type': result.event_type if hasattr(result, 'event_type') else None,
      'has_primes': primes_data is not None,
      'has_signups': signup_data is not None,
    }

  except Exception as e:
    print(f'Error fetching race details: {e}')
    return None


def fetch_team_with_cyclists(team_id: int):
  """Fetch team information and details about team members."""
  print(f'\nFetching team {team_id} with members...')
  print('-' * 60)

  zp = ZP()

  try:
    # Fetch team
    team = Team()
    team.set_session(zp)
    team.fetch(team_id)

    print(f'Team: {team.name}')
    print(f'Category: {team.category if hasattr(team, "category") else "N/A"}')

    # Optionally fetch details on team members
    # (This would require having member IDs)
    print(f'Members available: {hasattr(team, "members")}')

    return {
      'team_id': team_id,
      'name': team.name,
      'category': team.category if hasattr(team, 'category') else None,
      'has_members_data': hasattr(team, 'members'),
    }

  except Exception as e:
    print(f'Error fetching team: {e}')
    return None


def fetch_cyclist_profile_details(athlete_id: int):
  """Fetch comprehensive cyclist profile information."""
  print(f'\nFetching cyclist {athlete_id} profile...')
  print('-' * 60)

  zp = ZP()

  try:
    cyclist = Cyclist()
    cyclist.set_session(zp)
    cyclist.fetch(athlete_id)

    profile_info = {
      'athlete_id': athlete_id,
      'name': cyclist.name,
      'team': cyclist.team if hasattr(cyclist, 'team') else 'Unknown',
      'power_meter': cyclist.power_meter if hasattr(cyclist, 'power_meter') else False,
      'fields': list(cyclist.json().keys()),
    }

    print(f'Cyclist: {profile_info["name"]}')
    print(f'Team: {profile_info["team"]}')
    print(f'Power Meter: {profile_info["power_meter"]}')
    print(f'Profile fields: {len(profile_info["fields"])}')

    return profile_info

  except Exception as e:
    print(f'Error fetching cyclist: {e}')
    return None


def aggregate_race_statistics(race_ids: list[int]):
  """Fetch multiple races and aggregate statistics."""
  print(f'\nAggregating statistics for {len(race_ids)} races...')
  print('-' * 60)

  zp = ZP()
  races_with_details = []
  races_with_primes = 0
  races_with_signups = 0

  for i, race_id in enumerate(race_ids, 1):
    try:
      result = Result()
      result.set_session(zp)
      result.fetch(race_id)

      primes = Primes()
      primes.set_session(zp)
      primes_data = primes.fetch(race_id)

      signup = Signup()
      signup.set_session(zp)
      signup_data = signup.fetch(race_id)

      race_info = {
        'race_id': race_id,
        'name': result.name,
        'has_primes': primes_data is not None,
        'has_signups': signup_data is not None,
      }

      races_with_details.append(race_info)

      if primes_data:
        races_with_primes += 1
      if signup_data:
        races_with_signups += 1

      print(f'[{i}/{len(race_ids)}] ✓ {result.name}')

    except Exception as e:
      print(f'[{i}/{len(race_ids)}] ✗ Error: {e}')

  print('\nStatistics:')
  print(f'  Total races: {len(races_with_details)}')
  print(f'  Races with primes: {races_with_primes}')
  print(f'  Races with signups: {races_with_signups}')

  return races_with_details


def main():
  """Demonstrate advanced usage patterns."""
  print('Advanced Zwiftpower API Usage Examples')
  print('=' * 60)

  # ============================================================================
  # Example 1: Fetch race with all related data
  # ============================================================================
  print('\n1. Fetch Race with All Related Data')
  race_info = fetch_race_with_details(3590800)

  # ============================================================================
  # Example 2: Fetch team with member information
  # ============================================================================
  print('\n2. Fetch Team with Member Information')
  team_info = fetch_team_with_cyclists(456)

  # ============================================================================
  # Example 3: Comprehensive cyclist profile
  # ============================================================================
  print('\n3. Fetch Comprehensive Cyclist Profile')
  cyclist_info = fetch_cyclist_profile_details(123456)

  # ============================================================================
  # Example 4: Aggregate statistics across multiple races
  # ============================================================================
  print('\n4. Aggregate Statistics Across Multiple Races')
  race_ids = [3590800, 3590801, 3590802]
  race_stats = aggregate_race_statistics(race_ids)

  # ============================================================================
  # Summary
  # ============================================================================
  print('\n' + '=' * 60)
  print('Advanced examples completed!')
  print('\nKey patterns demonstrated:')
  print('1. Fetching related data from multiple endpoints')
  print('2. Combining data from different sources')
  print('3. Handling optional fields with hasattr()')
  print('4. Error handling and graceful degradation')
  print('5. Session reuse across multiple operations')


if __name__ == '__main__':
  main()
