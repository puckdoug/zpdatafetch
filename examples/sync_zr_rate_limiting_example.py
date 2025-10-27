#!/usr/bin/env python3
"""Example of using rate limiting with the synchronous zrdatafetch API.

This example demonstrates how to use the synchronous API with rate limiting
to respect API quotas. The API supports standard and premium rate limits.
"""

from zrdatafetch import ZR_obj, ZRRider


def main():
  """Demonstrate rate limiting with synchronous API."""
  print('Rate Limiting Example (Synchronous)')
  print('=' * 60)

  # ============================================================================
  # Example 1: Standard tier rate limiting (default)
  # ============================================================================
  print('\n1. Standard Tier Rate Limiting (Default)')
  print('-' * 60)
  print('Standard tier limits:')
  print('  - Riders GET: 5 requests per minute')
  print('  - Riders POST: 1 request per 15 minutes')
  print('  - Clubs: 1 request per 60 minutes')
  print('  - Results: 1 request per minute')

  rider = ZRRider(zwift_id=12345)
  print(f'\nRate limiter tier: {rider.rate_limiter.tier}')
  print(f'Rate limiter status: {rider.rate_limiter.get_status()}')

  # ============================================================================
  # Example 2: Premium tier rate limiting
  # ============================================================================
  print('\n2. Premium Tier Rate Limiting')
  print('-' * 60)
  print('Premium tier limits (10x higher for most endpoints):')
  print('  - Riders GET: 10 requests per minute')
  print('  - Riders POST: 10 requests per 15 minutes')
  print('  - Clubs: 10 requests per 60 minutes')
  print('  - Results: 1 request per minute (same as standard)')

  # Enable premium mode globally for all ZRRider instances
  ZR_obj.set_premium_mode(True)

  premium_rider = ZRRider(zwift_id=67890)
  print(f'\nRate limiter tier: {premium_rider.rate_limiter.tier}')
  print(f'Rate limiter status: {premium_rider.rate_limiter.get_status()}')

  # ============================================================================
  # Example 3: Batch fetching with rate limiting
  # ============================================================================
  print('\n3. Batch Fetching with Rate Limiting')
  print('-' * 60)

  # Reset to standard tier for demonstration
  ZR_obj.set_premium_mode(False)

  zwift_ids = [12345, 67890, 13579]

  print(f'\nFetching {len(zwift_ids)} riders with standard rate limits\n')

  for i, zwift_id in enumerate(zwift_ids, 1):
    try:
      rider = ZRRider(zwift_id=zwift_id)
      rider.fetch()

      status = rider.rate_limiter.get_status()
      riders_get = status['endpoints']['riders_get']

      print(
        f'[{i}/{len(zwift_ids)}] {rider.name}: '
        f'{riders_get["used"]}/{riders_get["limit"]} requests used',
      )

    except Exception as e:
      print(f'[{i}/{len(zwift_ids)}] Error: {e}')

  # ============================================================================
  # Example 4: Checking rate limit status before request
  # ============================================================================
  print('\n4. Checking Rate Limit Status')
  print('-' * 60)

  rider = ZRRider(zwift_id=12345)
  status = rider.rate_limiter.get_status()

  print('\nCurrent rate limit status:')
  print(f'  Tier: {status["tier"]}')

  for endpoint, ep_status in status['endpoints'].items():
    print(f'\n  {endpoint}:')
    print(f'    Used: {ep_status["used"]}/{ep_status["limit"]}')
    print(f'    Remaining: {ep_status["remaining"]}')
    print(f'    Window: {ep_status["window_seconds"]}s')
    print(f'    Resets in: {ep_status["reset_in_seconds"]:.1f}s')

  print('\n' + '=' * 60)
  print('Rate limiting examples completed!')


if __name__ == '__main__':
  main()
