#!/usr/bin/env python3
"""Example of concurrent fetching with the asynchronous zrdatafetch API.

This example demonstrates how to fetch data for multiple riders
concurrently using the async API, which is much faster than
sequential fetching.
"""

import asyncio
import time

from zrdatafetch import AsyncZR_obj, ZRRiderFetch


async def fetch_sequential(zwift_ids: list[int], zr: AsyncZR_obj):
  """Fetch rider data sequentially (slower)."""
  print("Sequential Fetching")
  print("-" * 60)
  start = time.time()

  riders_list = []
  for i, zwift_id in enumerate(zwift_ids, 1):
    try:
      print(f"  [{i}/{len(zwift_ids)}] Fetching rider {zwift_id}...")
      fetcher = ZRRiderFetch()
      fetcher.set_session(zr)
      riders = await fetcher.afetch(zwift_id)
      rider = riders[zwift_id]
      riders_list.append(rider)
      print(f"         ✓ {rider.name}")
    except Exception as e:
      print(f"         ✗ Error: {e}")

  elapsed = time.time() - start
  print(f"Sequential fetch completed in {elapsed:.2f} seconds")
  return riders_list


async def fetch_concurrent(zwift_ids: list[int], zr: AsyncZR_obj):
  """Fetch rider data concurrently (faster)."""
  print("Concurrent Fetching")
  print("-" * 60)
  start = time.time()

  async def fetch_one(zwift_id):
    try:
      fetcher = ZRRiderFetch()
      fetcher.set_session(zr)
      riders = await fetcher.afetch(zwift_id)
      return riders[zwift_id]
    except Exception as e:
      print(f"Error fetching {zwift_id}: {e}")
      return None

  print(f"Fetching {len(zwift_ids)} riders concurrently...")
  riders = await asyncio.gather(
    *[fetch_one(zwift_id) for zwift_id in zwift_ids],
  )

  # Filter out None results from failed fetches
  riders = [r for r in riders if r is not None]

  elapsed = time.time() - start
  print(f"Concurrent fetch completed in {elapsed:.2f} seconds")
  return riders


async def fetch_with_limited_concurrency(
  zwift_ids: list[int],
  zr: AsyncZR_obj,
  max_concurrent: int = 5,
):
  """Fetch with limited concurrency (rate limiting friendly)."""
  print(f"Limited Concurrency Fetching (max {max_concurrent} concurrent)")
  print("-" * 60)
  start = time.time()

  semaphore = asyncio.Semaphore(max_concurrent)

  async def fetch_one(zwift_id):
    async with semaphore:
      try:
        fetcher = ZRRiderFetch()
        fetcher.set_session(zr)
        riders = await fetcher.afetch(zwift_id)
        return riders[zwift_id]
      except Exception as e:
        print(f"Error fetching {zwift_id}: {e}")
        return None

  print(f"Fetching {len(zwift_ids)} riders with {max_concurrent} max concurrent...")
  riders = await asyncio.gather(
    *[fetch_one(zwift_id) for zwift_id in zwift_ids],
  )

  # Filter out None results from failed fetches
  riders = [r for r in riders if r is not None]

  elapsed = time.time() - start
  print(f"Limited concurrency fetch completed in {elapsed:.2f} seconds")
  return riders


async def fetch_using_batch(zwift_ids: list[int]):
  """Fetch using batch API (fastest, single request)."""
  print("Batch Fetching (Single API Call)")
  print("-" * 60)
  start = time.time()

  try:
    print(f"Fetching {len(zwift_ids)} riders in a single batch request...")
    riders_dict = await ZRRiderFetch.afetch_batch(*zwift_ids)
    riders_list = list(riders_dict.values())

    elapsed = time.time() - start
    print(f"Batch fetch completed in {elapsed:.2f} seconds")
    print(f"Successfully fetched {len(riders_list)} riders")
    return riders_list

  except Exception as e:
    print(f"Batch fetch error: {e}")
    return []


async def main():
  """Compare sequential vs concurrent fetching."""
  print("Comparing Sequential vs Concurrent Fetching")
  print("=" * 60)

  zwift_ids = [100000 + i for i in range(10)]

  async with AsyncZR_obj() as zr:
    # Sequential
    print("\n1. Sequential Approach")
    sequential_riders = await fetch_sequential(zwift_ids, zr)

    print()

    # Concurrent
    print("\n2. Concurrent Approach (All at once)")
    concurrent_riders = await fetch_concurrent(zwift_ids, zr)

    print()

    # Limited concurrency
    print("\n3. Limited Concurrency (Rate limiting friendly)")
    limited_riders = await fetch_with_limited_concurrency(
      zwift_ids,
      zr,
      max_concurrent=3,
    )

  print()

  # Batch (doesn't need shared session)
  print("\n4. Batch Approach (Fastest)")
  batch_riders = await fetch_using_batch(zwift_ids)

  print("\n" + "=" * 60)
  print("Summary")
  print("=" * 60)
  print(f"Sequential riders fetched: {len(sequential_riders)}")
  print(f"Concurrent riders fetched: {len(concurrent_riders)}")
  print(f"Limited concurrent riders fetched: {len(limited_riders)}")
  print(f"Batch riders fetched: {len(batch_riders)}")
  print("\nNote: Concurrent fetching is typically 3-5x faster!")
  print("Batch fetching is fastest (single API call) for large sets.")


if __name__ == "__main__":
  asyncio.run(main())
