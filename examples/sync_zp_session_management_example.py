#!/usr/bin/env python3
"""Example of session management with the synchronous zpdatafetch API.

This example demonstrates how to manage Zwiftpower sessions efficiently,
including session sharing and reuse across multiple data fetching objects.
"""

from zpdatafetch import ZP, Cyclist, Primes, Result, Team


def example_session_sharing():
  """Demonstrate session sharing across multiple objects."""
  print('\n1. Session Sharing')
  print('-' * 60)
  print('Create one session and share it across multiple data objects')

  # Create a single session
  zp = ZP()
  print('Created ZP session')

  # Create multiple data objects that share the session
  cyclist = Cyclist()
  result = Result()
  team = Team()

  # Set the same session for all objects
  cyclist.set_session(zp)
  result.set_session(zp)
  team.set_session(zp)

  print('Set session for: Cyclist, Result, Team')
  print('Now all objects use the same HTTP connection and cookies')

  # Fetch data from each object
  print('\nFetching data using shared session...')

  try:
    cyclist.fetch(123456)
    print(f'✓ Cyclist: {cyclist.name}')
  except Exception as e:
    print(f'✗ Cyclist error: {e}')

  try:
    result.fetch(3590800)
    print(f'✓ Result: {result.name}')
  except Exception as e:
    print(f'✗ Result error: {e}')

  try:
    team.fetch(456)
    print(f'✓ Team: {team.name}')
  except Exception as e:
    print(f'✗ Team error: {e}')

  print('\nBenefit: Shared connection pooling and cookies')


def example_multiple_sessions():
  """Demonstrate using multiple independent sessions."""
  print('\n2. Multiple Independent Sessions')
  print('-' * 60)
  print('Create separate sessions for different purposes')

  # Create separate sessions
  zp_session1 = ZP()
  zp_session2 = ZP()

  print('Created two independent ZP sessions')

  # Use first session for cyclists
  cyclist1 = Cyclist()
  cyclist1.set_session(zp_session1)

  # Use second session for results
  result1 = Result()
  result1.set_session(zp_session2)

  print('Session 1: Assigned to Cyclist')
  print('Session 2: Assigned to Result')

  print('\nBenefit: Isolation between different data types/sources')


def example_session_reuse():
  """Demonstrate efficient session reuse."""
  print('\n3. Session Reuse')
  print('-' * 60)
  print('Create one session and reuse it for sequential operations')

  zp = ZP()
  print('Created ZP session')

  # Fetch multiple cyclists using the same session
  athlete_ids = [123456, 789012, 345678]
  print(f'\nFetching {len(athlete_ids)} cyclists using single session...\n')

  for i, athlete_id in enumerate(athlete_ids, 1):
    try:
      cyclist = Cyclist()
      cyclist.set_session(zp)  # Reuse the same session
      cyclist.fetch(athlete_id)
      print(f'  [{i}] ✓ {cyclist.name}')
    except Exception as e:
      print(f'  [{i}] ✗ Error: {e}')

  print('\nBenefit: Efficient connection pooling and reduced overhead')


def example_context_manager():
  """Demonstrate using context managers for automatic cleanup."""
  print('\n4. Context Manager Pattern')
  print('-' * 60)
  print('Use context manager for automatic session cleanup')

  # Context managers are used with AsyncZP for async code
  # For sync ZP, you can still manage sessions manually
  print('Note: Context managers are primarily used with AsyncZP')
  print('For synchronous code, sessions are managed automatically')

  # Example with explicit session management
  print('\nExample: Explicit session management')
  zp = ZP()

  try:
    cyclist = Cyclist()
    cyclist.set_session(zp)
    cyclist.fetch(123456)
    print(f'✓ Fetched: {cyclist.name}')
  finally:
    # Manual cleanup if needed
    print('Session cleanup (if needed)')


def example_error_handling():
  """Demonstrate error handling with sessions."""
  print('\n5. Error Handling with Sessions')
  print('-' * 60)

  zp = ZP()

  # Simulate fetching with error handling
  athlete_ids = [123456, 999999, 345678]  # 999999 is likely invalid

  print(f'Fetching {len(athlete_ids)} cyclists with error handling\n')

  successful = 0
  failed = 0

  for athlete_id in athlete_ids:
    try:
      cyclist = Cyclist()
      cyclist.set_session(zp)
      cyclist.fetch(athlete_id)
      print(f'✓ {athlete_id}: {cyclist.name}')
      successful += 1

    except Exception as e:
      print(f'✗ {athlete_id}: {type(e).__name__} - {e}')
      failed += 1

  print(f'\nResults: {successful} successful, {failed} failed')
  print('Session remains valid for subsequent operations')


def main():
  """Demonstrate various session management patterns."""
  print('Zwiftpower Session Management Examples')
  print('=' * 60)

  example_session_sharing()
  example_multiple_sessions()
  example_session_reuse()
  example_context_manager()
  example_error_handling()

  print('\n' + '=' * 60)
  print('Session management examples completed!')
  print('\nKey Takeaways:')
  print('1. Share sessions to improve performance')
  print('2. Use multiple sessions for isolation')
  print('3. Reuse sessions for sequential operations')
  print('4. Handle errors gracefully')


if __name__ == '__main__':
  main()
