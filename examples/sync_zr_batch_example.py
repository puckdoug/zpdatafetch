#!/usr/bin/env python3
"""Example of batch fetching with the synchronous zrdatafetch API.

This example demonstrates how to fetch data for multiple riders
sequentially using the synchronous API.
"""

from zrdatafetch import ZRRider


def main():
  """Fetch data for multiple riders sequentially."""
  print('Batch Fetching Example (Synchronous)')
  print('=' * 60)

  # List of Zwift IDs to fetch
  zwift_ids = [12345, 67890, 13579, 24680, 35791]

  riders_data = []

  print(f'\nFetching data for {len(zwift_ids)} riders...\n')

  for i, zwift_id in enumerate(zwift_ids, 1):
    try:
      print(f'  [{i}/{len(zwift_ids)}] Fetching rider {zwift_id}...')

      rider = ZRRider(zwift_id=zwift_id)
      rider.fetch()

      riders_data.append(
        {
          'zwift_id': zwift_id,
          'name': rider.name,
          'rating': rider.current_rating,
          'wins': rider.wins,
        }
      )

      print(f'         ✓ {rider.name} (Rating: {rider.current_rating})')

    except Exception as e:
      print(f'         ✗ Error: {e}')
      riders_data.append(
        {
          'zwift_id': zwift_id,
          'error': str(e),
        }
      )

  # Display summary
  print('\n' + '=' * 60)
  print('Summary')
  print('=' * 60)

  successful = [r for r in riders_data if 'name' in r]
  failed = [r for r in riders_data if 'error' in r]

  print(f'\nSuccessful: {len(successful)} riders')
  if successful:
    for rider_info in successful:
      print(
        f'  - {rider_info["name"]} (ID: {rider_info["zwift_id"]}) '
        f'Rating: {rider_info["rating"]}',
      )

  if failed:
    print(f'\nFailed: {len(failed)} riders')
    for rider_info in failed:
      print(f'  - ID: {rider_info["zwift_id"]} - {rider_info["error"]}')

  print('\n' + '=' * 60)
  print('Batch fetch completed!')


if __name__ == '__main__':
  main()
