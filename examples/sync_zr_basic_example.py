#!/usr/bin/env python3
"""Basic example of using the synchronous zrdatafetch API.

This example demonstrates how to fetch Zwiftracing data synchronously,
which is suitable for simple scripts and applications that don't need
concurrent operations.
"""

from zrdatafetch import ZRResult, ZRRider, ZRTeam


def main():
  """Fetch Zwiftracing data synchronously."""
  print('Zwiftracing Data Fetching Examples')
  print('=' * 60)

  # ============================================================================
  # Example 1: Fetch a single rider
  # ============================================================================
  print('\n1. Fetch a single rider')
  print('-' * 60)

  rider = ZRRider(zwift_id=12345)
  rider.fetch()

  print(f'Rider Name: {rider.name}')
  print(f'Current Rating: {rider.current_rating}')
  print(f'Wins: {rider.wins}')
  print(f'Podiums: {rider.podiums}')

  # ============================================================================
  # Example 2: Fetch race results
  # ============================================================================
  print('\n2. Fetch race results')
  print('-' * 60)

  result = ZRResult(result_id=3590800)
  result.fetch()

  print(f'Race ID: {result.result_id}')
  print(f'Category: {result.category}')
  print(f'Number of Finishers: {len(result.riders)}')

  if result.riders:
    first_place = result.riders[0]
    print(f'Winner: {first_place.name} (ID: {first_place.zwift_id})')
    if len(result.riders) > 1:
      second_place = result.riders[1]
      print(f'2nd Place: {second_place.name}')

  # ============================================================================
  # Example 3: Fetch team/club information
  # ============================================================================
  print('\n3. Fetch team/club information')
  print('-' * 60)

  team = ZRTeam(team_id=456)
  team.fetch()

  print(f'Team Name: {team.name}')
  print(f'Team ID: {team.team_id}')
  print(f'Number of Members: {len(team.riders)}')

  if team.riders:
    print('Top Members:')
    for i, member in enumerate(team.riders[:5], 1):
      print(f'  {i}. {member.name} - Rating: {member.current_rating}')

  # ============================================================================
  # Example 4: Get full JSON representation
  # ============================================================================
  print('\n4. Full JSON representation of rider')
  print('-' * 60)

  rider_json = rider.json()
  print(f'Number of fields: {len(rider_json)}')
  print(f'Keys: {list(rider_json.keys())[:5]}...')

  print('\n' + '=' * 60)
  print('Examples completed successfully!')


if __name__ == '__main__':
  main()
