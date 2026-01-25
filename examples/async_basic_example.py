#!/usr/bin/env python3
"""Basic example of using the async zpdatafetch API."""

import asyncio

from zpdatafetch import AsyncZP, Cyclist


async def main():
  """Fetch cyclist data asynchronously."""
  # Use async context manager for automatic cleanup
  async with AsyncZP() as zp:
    print('Logged in to Zwiftpower')

    # Create cyclist object and set session
    cyclist = Cyclist()
    cyclist.set_session(zp)

    # Fetch data for one or more cyclists using afetch
    print('Fetching cyclist data...')
    cyclists = await cyclist.afetch(123456)

    # Get the cyclist data from the returned dictionary
    cyclist_data = cyclists.get(123456)

    # Display results
    if cyclist_data:
      print('\nCyclist Data:')
      print(cyclist_data.asdict())
    else:
      print('\nNo cyclist data found')


if __name__ == '__main__':
  asyncio.run(main())
