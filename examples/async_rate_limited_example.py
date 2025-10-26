#!/usr/bin/env python3
"""Example of rate-limited concurrent fetching."""

import asyncio

from zpdatafetch import AsyncCyclist, AsyncZP


async def fetch_with_rate_limit(cyclist_ids: list[int], max_concurrent: int = 5):
  """Fetch cyclist data with concurrency limit.

  Args:
    cyclist_ids: List of Zwift IDs to fetch
    max_concurrent: Maximum number of concurrent requests (default: 5)
  """
  # Create semaphore to limit concurrency
  semaphore = asyncio.Semaphore(max_concurrent)

  async def fetch_one(zp, cyclist_id):
    """Fetch a single cyclist with semaphore."""
    async with semaphore:
      cyclist = AsyncCyclist()
      cyclist.set_session(zp)
      print(f'Fetching cyclist {cyclist_id}...')
      data = await cyclist.fetch(cyclist_id)
      print(f'✓ Fetched cyclist {cyclist_id}')
      return data

  async with AsyncZP() as zp:
    # Create tasks for all cyclists
    tasks = [fetch_one(zp, cid) for cid in cyclist_ids]

    # Gather all results (max_concurrent will run at a time)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successes and failures
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = len(results) - successes

    return successes, failures


async def main():
  """Demonstrate rate-limited fetching."""
  print('Rate-Limited Async Fetching Example')
  print('=' * 50)

  # Fetch 10 cyclists with max 3 concurrent requests
  cyclist_ids = [100000 + i for i in range(10)]

  print(f'\nFetching {len(cyclist_ids)} cyclists')
  print('Max concurrent requests: 3')
  print()

  successes, failures = await fetch_with_rate_limit(
    cyclist_ids,
    max_concurrent=3,
  )

  print()
  print('=' * 50)
  print(f'Results: {successes} successful, {failures} failed')


if __name__ == '__main__':
  asyncio.run(main())
