#!/usr/bin/env python3
"""Basic example of using the asynchronous zrdatafetch API.

This example demonstrates how to fetch Zwiftracing data asynchronously,
which is suitable for applications that need concurrent operations.
"""

import asyncio

from zrdatafetch import AsyncZR_obj, ZRResultFetch, ZRRiderFetch, ZRTeamFetch


async def main() -> None:
  """Fetch Zwiftracing data asynchronously."""
  print('Zwiftracing Async Data Fetching Examples')
  print('=' * 60)

  async with AsyncZR_obj() as zr:
    # ==========================================================================
    # Example 1: Fetch a single rider
    # ==========================================================================
    print('\n1. Fetch a single rider')
    print('-' * 60)

    fetcher = ZRRiderFetch()
    fetcher.set_session(zr)
    riders = await fetcher.afetch(12345)  # Returns dict[int, ZRRiderRating]
    rider = riders[12345]

    print(f'Rider Name: {rider.name}')
    print(f'Current Rating: {rider.current_rating}')
    print(f'Current Rank: {rider.current_rank}')
    print(f'DRS Rating: {rider.drs_rating}')

    # ==========================================================================
    # Example 2: Fetch race results
    # ==========================================================================
    print('\n2. Fetch race results')
    print('-' * 60)

    result_fetcher = ZRResultFetch()
    result_fetcher.set_session(zr)
    # Returns dict[int, ZRRaceResult]
    results = await result_fetcher.afetch(3590800)
    result = results[3590800]

    print(f'Race ID: {result.race_id}')
    print(f'Event Title: {result.event_title}')
    print(f'Number of Finishers: {len(result)}')

    if len(result) > 0:
      first_place = result[0]
      print(f'Winner: Rider ID {first_place.zwift_id}')
      print(f'Winner Category: {first_place.category}')
      if len(result) > 1:
        second_place = result[1]
        print(f'2nd Place: Rider ID {second_place.zwift_id}')

    # ==========================================================================
    # Example 3: Fetch team/club information
    # ==========================================================================
    print('\n3. Fetch team/club information')
    print('-' * 60)

    team_fetcher = ZRTeamFetch()
    team_fetcher.set_session(zr)
    teams = await team_fetcher.afetch(456)  # Returns dict[int, ZRTeamRoster]
    team = teams[456]

    print(f'Team Name: {team.team_name}')
    print(f'Team ID: {team.team_id}')
    print(f'Number of Members: {len(team)}')

    if len(team) > 0:
      print('Top Members:')
      for i, member in enumerate(team[:5], 1):
        print(f'  {i}. {member.name} - Rating: {member.current_rating}')

    # ==========================================================================
    # Example 4: Get full dict representation
    # ==========================================================================
    print('\n4. Full dict representation of rider')
    print('-' * 60)

    rider_dict = rider.asdict()
    print(f'Number of fields: {len(rider_dict)}')
    print(f'Keys: {list(rider_dict.keys())[:5]}...')

  print('\n' + '=' * 60)
  print('Async examples completed successfully!')


if __name__ == '__main__':
  asyncio.run(main())
