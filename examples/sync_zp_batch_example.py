#!/usr/bin/env python3
"""Example of batch fetching with the synchronous zpdatafetch API.

This example demonstrates how to fetch data for multiple cyclists
and race results sequentially using the synchronous API.
"""

from zpdatafetch import ZP, Cyclist, Result


def fetch_multiple_cyclists(athlete_ids: list[int]):
  """Fetch data for multiple cyclists sequentially.

  Args:
    athlete_ids: List of Zwiftpower athlete IDs to fetch

  Returns:
    List of cyclist data dictionaries
  """
  print(f'Fetching data for {len(athlete_ids)} cyclists...\n')

  zp = ZP()
  cyclists_data = []

  for i, athlete_id in enumerate(athlete_ids, 1):
    try:
      print(f'  [{i}/{len(athlete_ids)}] Fetching cyclist {athlete_id}...')

      cyclist = Cyclist()
      cyclist.set_session(zp)
      cyclist.fetch(athlete_id)

      cyclists_data.append(
        {
          'athlete_id': athlete_id,
          'name': cyclist.name,
          'team': cyclist.team if hasattr(cyclist, 'team') else 'N/A',
          'power_meter': cyclist.power_meter
          if hasattr(cyclist, 'power_meter')
          else False,
        }
      )

      print(f'         ✓ {cyclist.name}')

    except Exception as e:
      print(f'         ✗ Error: {e}')
      cyclists_data.append(
        {
          'athlete_id': athlete_id,
          'error': str(e),
        }
      )

  return cyclists_data


def fetch_multiple_results(race_ids: list[int]):
  """Fetch data for multiple race results sequentially.

  Args:
    race_ids: List of Zwiftpower race IDs to fetch

  Returns:
    List of race result data dictionaries
  """
  print(f'Fetching data for {len(race_ids)} races...\n')

  zp = ZP()
  results_data = []

  for i, race_id in enumerate(race_ids, 1):
    try:
      print(f'  [{i}/{len(race_ids)}] Fetching race {race_id}...')

      result = Result()
      result.set_session(zp)
      result.fetch(race_id)

      results_data.append(
        {
          'race_id': race_id,
          'name': result.name,
          'category': result.category if hasattr(result, 'category') else 'N/A',
          'event_type': result.event_type if hasattr(result, 'event_type') else 'N/A',
        }
      )

      print(f'         ✓ {result.name}')

    except Exception as e:
      print(f'         ✗ Error: {e}')
      results_data.append(
        {
          'race_id': race_id,
          'error': str(e),
        }
      )

  return results_data


def main():
  """Demonstrate batch fetching with synchronous API."""
  print('Batch Fetching Example (Synchronous)')
  print('=' * 60)

  # ============================================================================
  # Example 1: Fetch multiple cyclists
  # ============================================================================
  print('\n1. Fetching Multiple Cyclists')
  print('-' * 60)

  athlete_ids = [123456, 789012, 345678, 901234, 567890]
  cyclists_data = fetch_multiple_cyclists(athlete_ids)

  # Display summary
  print('\n' + '=' * 60)
  print('Cyclists Summary')
  print('=' * 60)

  successful = [c for c in cyclists_data if 'name' in c]
  failed = [c for c in cyclists_data if 'error' in c]

  print(f'\nSuccessful: {len(successful)} cyclists')
  if successful:
    for cyclist_info in successful:
      power_meter = '✓' if cyclist_info['power_meter'] else '✗'
      print(
        f'  - {cyclist_info["name"]} (ID: {cyclist_info["athlete_id"]}) '
        f'Team: {cyclist_info["team"]} Power: {power_meter}',
      )

  if failed:
    print(f'\nFailed: {len(failed)} cyclists')
    for cyclist_info in failed:
      print(f'  - ID: {cyclist_info["athlete_id"]} - {cyclist_info["error"]}')

  # ============================================================================
  # Example 2: Fetch multiple race results
  # ============================================================================
  print('\n\n2. Fetching Multiple Race Results')
  print('-' * 60)

  race_ids = [3590800, 3590801, 3590802, 3590803, 3590804]
  results_data = fetch_multiple_results(race_ids)

  # Display summary
  print('\n' + '=' * 60)
  print('Race Results Summary')
  print('=' * 60)

  successful = [r for r in results_data if 'name' in r]
  failed = [r for r in results_data if 'error' in r]

  print(f'\nSuccessful: {len(successful)} races')
  if successful:
    for result_info in successful:
      print(
        f'  - {result_info["name"]} (ID: {result_info["race_id"]}) '
        f'Category: {result_info["category"]} Type: {result_info["event_type"]}',
      )

  if failed:
    print(f'\nFailed: {len(failed)} races')
    for result_info in failed:
      print(f'  - ID: {result_info["race_id"]} - {result_info["error"]}')

  print('\n' + '=' * 60)
  print('Batch fetch completed!')


if __name__ == '__main__':
  main()
