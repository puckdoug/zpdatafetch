# zpdatafetch

A python library and command-line tool for fetching data from zwiftpower.

## Installation

```sh
pip install zpdatafetch
```

or

```sh
uv add zpdatafetch
```

This currently works with python versions 3.10 - 3.14 including 3.14t but excluding 3.13t. Build fails on 3.13t and I am unlikely to fix it. If you want free threading, use 3.14t.

Note that while this builds and runs, it'd not yet properly tested to run in a real free-threaded environment.

## Usage

zpdatafetch comes with a command-line tool named `zpdata`. This can be used to
fetch data directly from zwiftpower. It sends the response to stdout. It can
also act as a guide for how to use the library in your own program.

For both command-line and library usage, you will need to have a zwiftpower
account. You will need set up your credentials in your system keyring. This can
be done using the following commands from they python keyring library (installed
as part of zpdatafetch if not already available on your system):

```sh
keyring set zpdatafetch username
keyring set zpdatafetch password
```

In principle, the library can use alternate backend keyrings, but I have not
tested this so far. At the moment, only the system keyring is used. See [the
keyring docs](https://keyring.readthedocs.io/en/latest/) for more details on how
to use the keyring and keyring library for your system.

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

### Library example

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

The ZP class is the main driver for the library. It is used to fetch the data
from zwiftpower. The other classes are used to parse the data into a more useful
format.

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

- [ ] Improve github actions setup
- [ ] Check if there are any objects not handled
- [ ] Update the interface to allow alternate keyrings
