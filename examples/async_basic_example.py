#!/usr/bin/env python3
"""Basic example of using the async zpdatafetch API."""

import asyncio

from zpdatafetch import AsyncCyclist, AsyncZP


async def main():
  """Fetch cyclist data asynchronously."""
  # Use async context manager for automatic cleanup
  async with AsyncZP() as zp:
    print('Logged in to Zwiftpower')

    # Create cyclist object and set session
    cyclist = AsyncCyclist()
    cyclist.set_session(zp)

    # Fetch data for one or more cyclists
    print('Fetching cyclist data...')
    data = await cyclist.fetch(123456)

    # Display results
    print('\nCyclist Data:')
    print(cyclist.json())


if __name__ == '__main__':
  asyncio.run(main())
