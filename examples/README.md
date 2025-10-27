# Examples

This directory contains examples for using both the `zrdatafetch` and `zpdatafetch` libraries.

## Overview

The examples are organized by library and API type (synchronous vs asynchronous):

- **zrdatafetch**: Library for Zwiftracing API (rider ratings, race results, teams)
- **zpdatafetch**: Library for Zwiftpower API (cyclist profiles, race results, signups)

## Zwiftracing (zrdatafetch) Examples

### Synchronous API

#### 1. **sync_zr_basic_example.py**

Basic usage of the synchronous zrdatafetch API.

**Topics covered:**

- Fetch a single rider
- Fetch race results
- Fetch team/club information
- Get full JSON representation

**Usage:**

```bash
python examples/sync_zr_basic_example.py
```

#### 2. **sync_zr_batch_example.py**

Batch fetching multiple riders sequentially.

**Topics covered:**

- Fetch data for multiple riders
- Error handling for failed requests
- Collecting and summarizing results
- Display success/failure statistics

**Usage:**

```bash
python examples/sync_zr_batch_example.py
```

#### 3. **sync_zr_rate_limiting_example.py**

Working with rate limits and premium tier support.

**Topics covered:**

- Standard tier rate limiting (default)
- Premium tier rate limiting (10x higher limits on most endpoints)
- Enabling premium mode globally
- Checking rate limit status
- Batch fetching with rate limit tracking

**Usage:**

```bash
python examples/sync_zr_rate_limiting_example.py
```

### Asynchronous API

#### 1. **async_zr_basic_example.py**

Basic usage of the asynchronous zrdatafetch API.

**Topics covered:**

- Async fetch of a single rider
- Async fetch of race results
- Async fetch of team information
- Get full JSON representation

**Usage:**

```bash
python examples/async_zr_basic_example.py
```

#### 2. **async_zr_concurrent_example.py**

Concurrent fetching with the asynchronous API.

**Topics covered:**

- Sequential fetching (slow)
- Concurrent fetching (fast - 3-5x faster)
- Limited concurrency (rate limiting friendly)
- Performance comparison
- Using `asyncio.gather()` for concurrent operations
- Semaphores for limiting concurrency

**Usage:**

```bash
python examples/async_zr_concurrent_example.py
```

## Zwiftpower (zpdatafetch) Examples

### Synchronous API

#### 1. **sync_zp_basic_example.py**

Basic usage of the synchronous zpdatafetch API.

**Topics covered:**

- Login to Zwiftpower
- Fetch a cyclist's profile
- Fetch race results
- Fetch team information
- Fetch race signups
- Get full JSON representation

**Usage:**

```bash
python examples/sync_zp_basic_example.py
```

**Note:** Requires Zwiftpower authentication credentials configured.

#### 2. **sync_zp_batch_example.py**

Batch fetching multiple cyclists and races sequentially.

**Topics covered:**

- Fetch data for multiple cyclists
- Fetch data for multiple race results
- Error handling and error recovery
- Displaying results summary with success/failure counts
- Accessing optional fields with `hasattr()`

**Usage:**

```bash
python examples/sync_zp_batch_example.py
```

#### 3. **sync_zp_session_management_example.py**

Session management patterns for efficient resource usage.

**Topics covered:**

- Session sharing across multiple data objects
- Multiple independent sessions
- Session reuse for sequential operations
- Context manager patterns
- Error handling with sessions

**Usage:**

```bash
python examples/sync_zp_session_management_example.py
```

#### 4. **sync_zp_advanced_example.py**

Advanced usage patterns combining multiple data sources.

**Topics covered:**

- Fetch race with all related data (results + primes + signups)
- Fetch team with member information
- Comprehensive cyclist profile fetching
- Aggregating statistics across multiple races
- Combining data from multiple endpoints

**Usage:**

```bash
python examples/sync_zp_advanced_example.py
```

### Asynchronous API

The asynchronous examples for zpdatafetch are in the root examples directory:

#### 1. **async_basic_example.py**

Basic usage of the asynchronous zpdatafetch API.

#### 2. **async_concurrent_example.py**

Concurrent fetching with the asynchronous API.

#### 3. **async_rate_limited_example.py**

Rate-limited concurrent fetching.

## Quick Start Guide

### For Zwiftracing (zrdatafetch)

**Synchronous (simple scripts):**

```python
from zrdatafetch import ZRRider

rider = ZRRider(zwift_id=12345)
rider.fetch()
print(f"Rider: {rider.name}, Rating: {rider.current_rating}")
```

**Asynchronous (concurrent operations):**

```python
import asyncio
from zrdatafetch import AsyncZRRider

async def main():
    rider = AsyncZRRider(zwift_id=12345)
    await rider.fetch()
    print(f"Rider: {rider.name}, Rating: {rider.current_rating}")

asyncio.run(main())
```

### For Zwiftpower (zpdatafetch)

**Synchronous:**

```python
from zpdatafetch import ZP, Cyclist

zp = ZP()
cyclist = Cyclist()
cyclist.set_session(zp)
cyclist.fetch(123456)
print(f"Cyclist: {cyclist.name}, Team: {cyclist.team}")
```

**Asynchronous:**

```python
import asyncio
from zpdatafetch import AsyncZP, AsyncCyclist

async def main():
    async with AsyncZP() as zp:
        cyclist = AsyncCyclist()
        cyclist.set_session(zp)
        await cyclist.fetch(123456)
        print(f"Cyclist: {cyclist.name}")

asyncio.run(main())
```

## Common Patterns

### Error Handling

```python
try:
    rider.fetch()
except Exception as e:
    print(f"Error: {e}")
```

### Checking Optional Fields

```python
if hasattr(rider, 'some_field'):
    value = rider.some_field
else:
    value = 'Not available'
```

### Session Sharing

```python
zp = ZP()
cyclist = Cyclist()
result = Result()

# Both share the same session
cyclist.set_session(zp)
result.set_session(zp)
```

### Rate Limiting (zrdatafetch)

```python
from zrdatafetch import ZR_obj

# Enable premium tier
ZR_obj.set_premium_mode(True)

# Now all new instances use premium limits
rider = ZRRider(zwift_id=12345)
rider.fetch()
```

## Configuration

See the main README.md for configuration options:

- API credentials
- Logging setup
- Rate limiting settings

## Dependencies

All examples require the respective libraries to be installed:

```bash
pip install zrdatafetch zpdatafetch
```

Or in development mode:

```bash
pip install -e .
```

## License

These examples are provided as part of the zpdatafetch project.
See the main LICENSE file for details.
