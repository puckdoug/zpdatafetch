#!/usr/bin/env python3
"""Basic example of using the synchronous zrdatafetch API.

This example demonstrates how to fetch Zwiftracing data synchronously,
which is suitable for simple scripts and applications that don't need
concurrent operations.
"""

from zrdatafetch import ZRResultFetch, ZRRiderFetch, ZRTeamFetch


def main():
  """Fetch Zwiftracing data synchronously."""
  print('Zwiftracing Data Fetching Examples')
  print('=' * 60)

  # ============================================================================
  # Example 1: Fetch a single rider
  # ============================================================================
  print('\n1. Fetch a single rider')
  print('-' * 60)

  rider_fetcher = ZRRiderFetch()
  riders = rider_fetcher.fetch(12345)
  rider = riders[12345]

  print(f'Rider Name: {rider.name}')
  print(f'Current Rating: {rider.current_rating}')
  print(f'Current Rank: {rider.current_rank}')

  # ============================================================================
  # Example 2: Fetch race results
  # ============================================================================
  print('\n2. Fetch race results')
  print('-' * 60)

  result_fetcher = ZRResultFetch()
  results = result_fetcher.fetch(3590800)
  result = results[3590800]

  print(f'Race ID: {result.race_id}')
  print(f'Number of Finishers: {len(result)}')

  if len(result) > 0:
    first_place = result[0]
    print(f'Winner: {first_place.name} (ID: {first_place.zwift_id})')
    if len(result) > 1:
      second_place = result[1]
      print(f'2nd Place: {second_place.name}')

  # ============================================================================
  # Example 3: Fetch team/club information
  # ============================================================================
  print('\n3. Fetch team/club information')
  print('-' * 60)

  team_fetcher = ZRTeamFetch()
  teams = team_fetcher.fetch(456)
  team = teams[456]

  print(f'Team Name: {team.name}')
  print(f'Team ID: {team.team_id}')
  print(f'Number of Members: {len(team)}')

  if len(team) > 0:
    print('Top Members:')
    for i, member in enumerate(list(team)[:5], 1):
      print(f'  {i}. {member.name} - Rating: {member.current_rating}')

  # ============================================================================
  # Example 4: Get dictionary representation
  # ============================================================================
  print('\n4. Dictionary representation of rider')
  print('-' * 60)

  rider_dict = rider.asdict()
  print(f'Number of fields: {len(rider_dict)}')
  print(f'Keys: {list(rider_dict.keys())[:5]}...')

  print('\n' + '=' * 60)
  print('Examples completed successfully!')


if __name__ == '__main__':
  main()
