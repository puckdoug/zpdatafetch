#!/usr/bin/env python3
"""Example of concurrent fetching with the asynchronous zrdatafetch API.

This example demonstrates how to fetch data for multiple riders
concurrently using the async API, which is much faster than
sequential fetching.
"""

import asyncio
import time

from zrdatafetch import AsyncZRResult, AsyncZRRider, AsyncZRTeam


async def fetch_sequential(zwift_ids: list[int]):
  """Fetch rider data sequentially (slower)."""
  print('Sequential Fetching')
  print('-' * 60)
  start = time.time()

  riders = []
  for i, zwift_id in enumerate(zwift_ids, 1):
    try:
      print(f'  [{i}/{len(zwift_ids)}] Fetching rider {zwift_id}...')
      rider = AsyncZRRider(zwift_id=zwift_id)
      await rider.fetch()
      riders.append(rider)
      print(f'         ✓ {rider.name}')
    except Exception as e:
      print(f'         ✗ Error: {e}')

  elapsed = time.time() - start
  print(f'Sequential fetch completed in {elapsed:.2f} seconds')
  return riders


async def fetch_concurrent(zwift_ids: list[int]):
  """Fetch rider data concurrently (faster)."""
  print('Concurrent Fetching')
  print('-' * 60)
  start = time.time()

  async def fetch_one(zwift_id):
    try:
      rider = AsyncZRRider(zwift_id=zwift_id)
      await rider.fetch()
      return rider
    except Exception as e:
      print(f'Error fetching {zwift_id}: {e}')
      return None

  print(f'Fetching {len(zwift_ids)} riders concurrently...')
  riders = await asyncio.gather(
    *[fetch_one(zwift_id) for zwift_id in zwift_ids],
  )

  # Filter out None results from failed fetches
  riders = [r for r in riders if r is not None]

  elapsed = time.time() - start
  print(f'Concurrent fetch completed in {elapsed:.2f} seconds')
  return riders


async def fetch_with_limited_concurrency(
  zwift_ids: list[int],
  max_concurrent: int = 5,
):
  """Fetch with limited concurrency (rate limiting friendly)."""
  print(f'Limited Concurrency Fetching (max {max_concurrent} concurrent)')
  print('-' * 60)
  start = time.time()

  semaphore = asyncio.Semaphore(max_concurrent)

  async def fetch_one(zwift_id):
    async with semaphore:
      try:
        rider = AsyncZRRider(zwift_id=zwift_id)
        await rider.fetch()
        return rider
      except Exception as e:
        print(f'Error fetching {zwift_id}: {e}')
        return None

  print(f'Fetching {len(zwift_ids)} riders with {max_concurrent} max concurrent...')
  riders = await asyncio.gather(
    *[fetch_one(zwift_id) for zwift_id in zwift_ids],
  )

  # Filter out None results from failed fetches
  riders = [r for r in riders if r is not None]

  elapsed = time.time() - start
  print(f'Limited concurrency fetch completed in {elapsed:.2f} seconds')
  return riders


async def main():
  """Compare sequential vs concurrent fetching."""
  print('Comparing Sequential vs Concurrent Fetching')
  print('=' * 60)

  zwift_ids = [100000 + i for i in range(10)]

  # Sequential
  print('\n1. Sequential Approach')
  sequential_riders = await fetch_sequential(zwift_ids)

  print()

  # Concurrent
  print('\n2. Concurrent Approach (All at once)')
  concurrent_riders = await fetch_concurrent(zwift_ids)

  print()

  # Limited concurrency
  print('\n3. Limited Concurrency (Rate limiting friendly)')
  limited_riders = await fetch_with_limited_concurrency(zwift_ids, max_concurrent=3)

  print('\n' + '=' * 60)
  print('Summary')
  print('=' * 60)
  print(f'Sequential riders fetched: {len(sequential_riders)}')
  print(f'Concurrent riders fetched: {len(concurrent_riders)}')
  print(f'Limited concurrent riders fetched: {len(limited_riders)}')
  print('\nNote: Concurrent fetching is typically 3-5x faster!')


if __name__ == '__main__':
  asyncio.run(main())
