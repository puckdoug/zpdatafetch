# zpdatafetch & zrdatafetch

A python library and command-line tool for fetching data from ZwiftPower.com and Zwiftracing.app APIs.

## Installation

```sh
pip install zpdatafetch
```

or

```sh
uv add zpdatafetch
```

This currently works with python versions 3.10 - 3.14 including 3.14t but excluding 3.13t. Build fails on 3.13t and I am unlikely to fix it. If you want free threading, use 3.14t.

Note that while this builds and runs, it'd not yet properly tested to run in a real free-threaded environment. Please do [report](https://github.com/puckdoug/zpdatafetch/issues) any issues you find.

## Overview

This package provides two main command-line tools:

| Tool         | API         | Purpose                              | Data Types                                |
| ------------ | ----------- | ------------------------------------ | ----------------------------------------- |
| **`zpdata`** | ZwiftPower  | Race rankings, signups, results      | Cyclist, Primes, Results, Signups, Teams  |
| **`zrdata`** | Zwiftracing | Rider ratings, race results, rosters | Rider Ratings, Race Results, Team Rosters |

Both tools support batch operations, flexible logging, and can be used as standalone CLI tools or imported as libraries. They maintain separate credential stores for each API.

## Key Features

### For zpdata (ZwiftPower)

- **Cyclist rankings** - Individual and batch lookups by Zwift ID
- **Race results** - Detailed finish information and point scoring
- **Signups** - Event signup lists and participant info
- **Primes/Sprints** - Intermediate results and prime tracking
- **Team data** - Team rosters and member information
- **Async support** - Concurrent fetching with asyncio or trio backends
- **Connection pooling** - Efficient batch operations with shared HTTP client

### For zrdata (Zwiftracing)

- **Rider ratings** - Current, max30, max90 ratings and categories
- **Batch POST requests** - Fetch up to 1000 riders in a single efficient API call
- **Derived rating scores** - Calculated DRS for all riders
- **Power metrics** - Zwiftracing compound score and power data
- **Race results** - Complete race result data with rating changes
- **Team rosters** - Full team member details and power metrics
- **File-based batch input** - Read rider IDs from files for batch processing
- **Safe testing** - `--noaction` flag to preview operations without network calls

### Common Features

- **Flexible logging** - Console and file logging with multiple levels (DEBUG, INFO, WARNING, ERROR)
- **Secure credentials** - System keyring integration for safe credential storage
- **CLI and library APIs** - Use as command-line tools or import as Python libraries
- **JSON output** - Raw JSON or formatted output for all data types
- **Error handling** - Comprehensive error messages and retry logic

## Credentials Setup

For ZwiftPower (`zpdata`), you will need a zwiftpower account with credentials in your system keyring:

```sh
keyring set zpdatafetch username
keyring set zpdatafetch password
```

For Zwiftracing (`zrdata`), you will need your Zwiftracing API authorization header:

```sh
keyring set zrdatafetch authorization
# Or use the CLI: zrdata config
```

In principle, the library can use alternate backend keyrings, but I have not
tested this so far. At the moment, only the system keyring is used. See [the
keyring docs](https://keyring.readthedocs.io/en/latest/) for more details on how
to use the keyring and keyring library for your system.

## ZwiftPower Data (zpdata)

The `zpdata` command-line tool provides access to ZwiftPower data including cyclist rankings, race results, and event signups.

### Command-line example

```sh
usage: zpdata [-h] [-v] [-vv] [--log-file PATH] [-r] [{config,cyclist,primes,result,signup,team}] [id ...]

Module for fetching zwiftpower data using the Zwifpower API

positional arguments:
  {config,cyclist,primes,result,signup,team}
                        which command to run
  id                    the id to search for, ignored for config

options:
  -h, --help            show this help message and exit
  -v, --verbose         enable INFO level logging to console
  -vv, --debug          enable DEBUG level logging to console
  --log-file PATH       path to log file (enables file logging)
  -r, --raw             print the raw results returned to screen
```

**Basic usage:**

```sh
# Fetch cyclist data (quiet mode - only errors shown)
zpdata cyclist 1234567

# Verbose mode - show INFO messages
zpdata -v cyclist 1234567

# Debug mode - show DEBUG messages
zpdata -vv cyclist 1234567

# Log to file only (quiet console)
zpdata --log-file zpdatafetch.log cyclist 1234567

# Both console and file logging
zpdata -v --log-file zpdatafetch.log cyclist 1234567
```

### Library example (Synchronous API)

```python
from zpdatafetch import Cyclist

c = Cyclist()
c.fetch(1234567) # fetch data for cyclist with zwift id 1234567
print(c.json())
```

The interface for each of the objects is effectively the same as the example
above, with the individual class and id number changed as appropriate. The
available classes are as follows:

- Cyclist: fetch one or more cyclists by zwift id
- Primes: fetch primes from one or more races using event id
- Result: fetch results from one or more races (finish, points) using event id
- Signup: fetch signups for a particular event by event id
- Team: fetch team data by team id

## Zwiftracing Data (zrdata)

The `zrdata` command-line tool provides access to Zwiftracing API data including rider ratings, race results, and team rosters.

### Command-line usage

```sh
usage: zrdata [-h] [-v] [-vv] [--log-file PATH] [-r] [--noaction] [--batch] [--batch-file FILE]
              [{config,rider,result,team}] [id ...]

Module for fetching Zwiftracing data using the Zwiftracing API

positional arguments:
  {config,rider,result,team}
                        which command to run
  id                    the id to search for

options:
  -h, --help            show this help message and exit
  -v, --verbose         enable INFO level logging to console
  -vv, --debug          enable DEBUG level logging to console
  --log-file PATH       path to log file (enables file logging)
  -r, --raw             print the raw results returned to screen
  --noaction            report what would be done without actually fetching data
  --batch               use batch POST endpoint for multiple IDs (rider command only)
  --batch-file FILE     read IDs from file (one per line) for batch request (rider command only)
```

### Basic Examples

```sh
# Fetch a single rider's rating data
zrdata rider 12345

# Fetch multiple riders individually (GET requests)
zrdata rider 12345 67890 11111

# Fetch multiple riders using batch POST endpoint (more efficient)
zrdata rider --batch 12345 67890 11111

# Fetch riders from a file
zrdata rider --batch-file riders.txt

# Fetch race results
zrdata result 3590800

# Fetch team roster
zrdata team 456

# View current configuration
zrdata config

# Set up authorization
zrdata config  # Will prompt for authorization header
```

### Advanced Options

```sh
# Verbose output with debug logging
zrdata -vv rider 12345

# Raw JSON output
zrdata -r rider 12345

# Test what would be fetched without making requests
zrdata --noaction --batch 12345 67890

# Log to file
zrdata --log-file zrdata.log rider 12345

# Combine options
zrdata -v --batch -r rider 12345 67890 11111
```

### Batch Processing

For efficiency, `zrdata` supports batch operations that use the Zwiftracing API's POST endpoints:

**Command-line batch:**

```sh
# Batch with inline IDs (up to 1000 per request)
zrdata rider --batch 123 456 789

# Batch from file
cat > riders.txt << EOF
12345
67890
11111
EOF
zrdata rider --batch-file riders.txt
```

**Programmatic batch (Python):**

```python
from zrdatafetch import ZRRider

# Batch fetch multiple riders in one API request
riders = ZRRider.fetch_batch(12345, 67890, 11111)
for zwift_id, rider in riders.items():
    print(f"{rider.name}: {rider.current_rating}")
```

### Library Usage

```python
from zrdatafetch import ZRRider, ZRResult, ZRTeam

# Fetch single rider
rider = ZRRider(zwift_id=12345)
rider.fetch()
print(rider.json())

# Fetch batch of riders (more efficient)
riders = ZRRider.fetch_batch(12345, 67890, 11111)
for zwift_id, rider in riders.items():
    print(f"{rider.name} - Rating: {rider.current_rating}")

# Fetch race results
result = ZRResult(race_id=3590800)
result.fetch()
print(f"Found {len(result.results)} riders")

# Fetch team roster
team = ZRTeam(team_id=456)
team.fetch()
print(f"Team: {team.team_name}")
for rider in team.riders:
    print(f"  {rider.name}: {rider.current_rating}")
```

### Data Classes

**ZRRider**: Individual rider rating data

- `zwift_id`: Rider's Zwift ID
- `name`: Rider's display name
- `current_rating`: Current rating score
- `current_rank`: Current category rank (A, B, C, D, etc.)
- `max30_rating`: Best rating in last 30 days
- `max30_rank`: Category for max30
- `max90_rating`: Best rating in last 90 days
- `max90_rank`: Category for max90
- `drs_rating`: Derived rating score (max30 or max90)
- `drs_rank`: Category for DRS
- `gender`: Rider gender (M/F)
- `zrcs`: Zwiftracing compound score (power metric)

**ZRResult**: Race result data

- `race_id`: The race ID (Zwift event ID)
- `results`: List of rider results with positions and rating changes

**ZRTeam**: Team roster data

- `team_id`: Team/club ID
- `team_name`: Team name
- `riders`: List of team members with their ratings and power metrics

### Configuration

To set up Zwiftracing API authorization:

```sh
# Interactive setup
zrdata config

# Or set directly in keyring
keyring set zrdatafetch authorization
# Then enter your Zwiftracing API authorization header
```

### Async Library example

The library also provides a full async/await API for concurrent operations:

```python
import anyio
from zpdatafetch import AsyncCyclist, AsyncResult, AsyncZP

async def main():
    # Use async context manager
    async with AsyncZP() as zp:
        cyclist = AsyncCyclist()
        result = AsyncResult()

        cyclist.set_session(zp)
        result.set_session(zp)

        # Fetch multiple resources concurrently
        async with anyio.create_task_group() as tg:
            tg.start_soon(cyclist.fetch, 1234567, 7654321)  # Multiple cyclists
            tg.start_soon(result.fetch, 3590800, 3590801)   # Multiple races

        print(cyclist.json())
        print(result.json())

anyio.run(main)
```

**Available async classes:**

- AsyncZP: Async authentication and HTTP client
- AsyncCyclist: Async cyclist data fetching
- AsyncResult: Async race results fetching
- AsyncSignup: Async signup list fetching
- AsyncTeam: Async team data fetching
- AsyncPrimes: Async prime/sprint data fetching

**Async backend support:**

The async API uses [anyio](https://anyio.readthedocs.io/) to support both **asyncio** and **trio** backends:

- **asyncio** (default): Built into Python, widely used
- **trio** (optional): Install with `pip install zpdatafetch[trio]`

You can use either backend transparently - the same code works with both.

See `local/ASYNC_API_DOCUMENTATION.md` and `examples/async_*.py` for detailed async usage examples.

The ZP class is the main driver for the library. It is used to fetch the data
from zwiftpower. The other classes are used to parse the data into a more useful
format.

#### Context Manager (Resource Management)

The library now supports context managers for automatic resource cleanup. This is especially useful when making multiple requests, as it ensures proper cleanup of the underlying HTTP session:

```python
from zpdatafetch import Cyclist

# Using context manager for automatic cleanup
with Cyclist() as c:
    c.fetch([1234567, 7654321])  # fetch multiple cyclists
    print(c.json())
# HTTP session is automatically closed
```

#### Connection Pooling (Performance Optimization)

For batch operations, you can enable connection pooling to reuse a single HTTP client across multiple requests. This significantly improves performance when making multiple API calls:

```python
from zpdatafetch import Cyclist, Result

# Multiple operations share a single connection pool
with Cyclist(shared_client=True) as cyclist:
    cyclist.fetch([1234567, 7654321, 9876543])
    cyclist_data = cyclist.json()

with Result(shared_client=True) as result:
    result.fetch([111111, 222222, 333333])
    result_data = result.json()

# Clean up shared session when done
from zpdatafetch.zp import ZP
ZP.close_shared_session()
```

The `shared_client=True` option (enabled by default) allows multiple instances to reuse the same HTTP connection pool, reducing overhead and improving throughput.

#### Automatic Retry with Exponential Backoff

The library includes built-in retry logic with exponential backoff for handling transient network failures. This is automatically applied to `fetch_json()` and `fetch_page()` methods:

```python
from zpdatafetch import Cyclist

c = Cyclist()

# Retries are automatically handled internally
# Default: 3 retries with exponential backoff
c.fetch(1234567)  # Automatically retries on transient errors
print(c.json())
```

For direct HTTP operations via the ZP class, you can configure retry behavior:

```python
from zpdatafetch.zp import ZP

zp = ZP()

# Fetch with custom retry settings
data = zp.fetch_json(
    '/some/endpoint',
    max_retries=5,           # number of retries
    backoff_factor=1.5       # exponential backoff multiplier
)
```

The retry mechanism automatically handles:

- Connection errors
- Timeout errors
- Request errors
- HTTP 5xx server errors

This makes the library more resilient to temporary network issues and server hiccups.

### Logging

zpdatafetch provides flexible logging support for both library and command-line usage.

#### Default Behavior (Quiet Mode)

By default, the library is completely quiet except for errors, which are sent to stderr. This ensures that library users get clean output unless something goes wrong.

#### Library Usage with Logging

To enable logging when using zpdatafetch as a library, use the `setup_logging()` function:

```python
from zpdatafetch import setup_logging, Cyclist

# Enable console logging at INFO level
setup_logging(console_level='INFO')

c = Cyclist()
c.fetch(1234567)
```

**Logging Configuration Options:**

```python
from zpdatafetch import setup_logging

# File logging only (no console output except errors)
setup_logging(log_file='zpdatafetch.log', force_console=False)

# Console logging at DEBUG level
setup_logging(console_level='DEBUG')

# Both console (INFO) and file (DEBUG) logging
setup_logging(
    log_file='debug.log',
    console_level='INFO',    # Simple messages to console
    file_level='DEBUG'       # Detailed logs to file
)

# Force console logging even when not in a TTY
setup_logging(console_level='INFO', force_console=True)
```

**Log Format:**

- **Console output**: Simple, clean format showing only messages (e.g., `"Logging in to Zwiftpower"`)
- **File output**: Detailed format with timestamps, module names, log levels, function names, and line numbers
  ```
  2025-10-24 15:17:39 - zpdatafetch.zp - INFO - login:90 - Logging in to Zwiftpower
  ```

**Available Log Levels:**

- `'DEBUG'` - Detailed diagnostic information
- `'INFO'` - General informational messages
- `'WARNING'` - Warning messages
- `'ERROR'` - Error messages (default)

### Object signature

Each object has a common set of methods available:

```python
obj.fetch(id) or obj.fetch([id1, id2, id3]) # fetch the data from zwiftpower. As argument, fetch expects a single ID or a list (tuple or array) of IDs.
obj.json() # return the data as a json object
obj.asdict() # return the data as a dictionary
print(obj) # effectively the same as obj.asdict()
```

## Development

I've switched over to using [https://astral.sh/](Astral)'s
[https://astral.sh/uv/](uv) for the development toolchain. Directions below try
to cover both options.

1. Install this package
2. Install the requirements

```sh
pip install -r requirements.txt
```

or

```sh
uv sync
```

3. Set up your keyring. You may want to use a account that is separate from the
   one you use for riding and racing for this.

```sh
keyring set zpdatafetch username
keyring set zpdatafetch password
```

4. Run the downloader

```sh
  PYTHONPATH=`pwd`/src python src/zpdatafetch/zp.py
```

or

```sh
  uv run src/zpdatafetch/zp.py
```

This should return a '200' message if you've set everything up correctly, proving that the program can log in correctly to Zwiftpower.

With a few exceptions, each object has a callable interface that can be used for
simple direct access to experiment without additional code wrapped around it -
yours or the provided command-line tool. They each respond to the -h flag to
provide help. Basic examples follow.

### Cyclist example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/cyclist.py -v -r <zwift_id>
```

### Team example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/team.py -v -r <team_id>
```

### Signup example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/signup.py -v -r <race_id>
```

### Result example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/result.py -v -r <race_id>
```

### Primes example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/primes.py -v -r <race_id>
```

5. Build the project

```sh
build
```

or

```sh
uvx --from build pyproject-build --installer uv
```

## To Do & Known Issues

While useful and usable, there's a bit that can be done to improve this package.
Anyone interested to contribute is welcome to do so. These are the areas where I
could use help:

- [ ] Check if there are any objects not handled
- [ ] Update the interface to allow alternate keyrings
