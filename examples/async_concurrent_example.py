#!/usr/bin/env python3
"""Example of concurrent fetching with the async API."""

import asyncio
import time

from zpdatafetch import AsyncZP, Cyclist, Result


async def fetch_sequential() -> None:
  """Fetch data sequentially (slower)."""
  print('\n=== Sequential Fetching ===')
  start = time.time()

  async with AsyncZP() as zp:
    # Create objects
    cyclist = Cyclist()
    result = Result()

    cyclist.set_session(zp)
    result.set_session(zp)

    # Fetch one at a time
    print('Fetching cyclists...')
    await cyclist.afetch(123456, 789012)

    print('Fetching race results...')
    await result.afetch(3590800, 3590801)

  elapsed = time.time() - start
  print(f'Sequential fetch completed in {elapsed:.2f} seconds')


async def fetch_concurrent() -> None:
  """Fetch data concurrently (faster)."""
  print('\n=== Concurrent Fetching ===')
  start = time.time()

  async with AsyncZP() as zp:
    # Create objects
    cyclist = Cyclist()
    result = Result()

    cyclist.set_session(zp)
    result.set_session(zp)

    # Fetch concurrently using asyncio.gather
    print('Fetching cyclists and results concurrently...')
    cyclist_data, result_data = await asyncio.gather(
      cyclist.afetch(123456, 789012),
      result.afetch(3590800, 3590801),
    )

    print(f'Fetched {len(cyclist_data)} cyclists')
    print(f'Fetched {len(result_data)} race results')

  elapsed = time.time() - start
  print(f'Concurrent fetch completed in {elapsed:.2f} seconds')


async def main() -> None:
  """Compare sequential vs concurrent fetching."""
  print('Comparing Sequential vs Concurrent Fetching')
  print('=' * 50)

  # Sequential
  await fetch_sequential()

  # Concurrent
  await fetch_concurrent()

  print('\n' + '=' * 50)
  print('Concurrent fetching is typically 2-3x faster!')


if __name__ == '__main__':
  asyncio.run(main())
