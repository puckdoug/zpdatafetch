# zpdatafetch

A python library for fetching data from zwiftpower

## Installation

```sh
pip install zpdatafetch
```

## Usage

zpdatafetch comes with a command-line tool named zpdata. This can be used to fetch data directly from zwiftpower. It sends the json response to stdout. It also acts as a guide for how to use the library in your own program.

For both command-line and library usage, you will need to have a zwiftpower account. You will need set up your credentials in the keyring. This can be done using the following commands:

```sh
keyring set zpdatafetch username
keyring set zpdatafetch password
```

### Command-line example

```sh
usage: zpdata [-h] [--verbose] [{config,cyclist,primes,result,signup,team}] [id ...]

Module for fetching zwiftpower data using the Zwifpower API

positional arguments:
  {config,cyclist,primes,result,signup,team}
                        which command to run
  id                    the id to search for, ignored for config

options:
  -h, --help            show this help message and exit
  -v, --verbose         provide feedback while running
```

### Library example

```python
from zpdatafetch import Cyclist

c = Cyclist()
c.verbose = True
c.fetch(12345) # fetch data for cyclist with zwift id 12345
print(c.raw)
```

The interface for each of the objects is effectively the same as the example above, with the individual class and id number changed as appropriate. The available classes are as follows:

- Cyclist: fetch one or more cyclists by zwift id
- Primes: fetch primes from one or more races using event id
- Result: fetch results from one or more races (finish, points) using event id
- Signup: fetch signups for a particular event by event id
- Team: fetch team data by team id

The classes ZP class is the main driver for the library. It is used to fetch the data from zwiftpower. The other classes are used to parse the data into a more useful format.

## development

1. Install this package
2. Install the requirements

```sh
pip install -r requirements.txt
```

3. Set up your keyring. You may want to use a separate account on zwiftpower for this.

```sh
keyring set zpdatafetch username
keyring set zpdatafetch password
```

4. Run the downloader

```sh
  PYTHONPATH=`pwd`/src python src/zpdatafetch/zp.py
```

## Cyclist example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/cyclist.py -v -r <zwift_id>
```

## Team example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/team.py -v -r <team_id>
```

## Signup example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/signup.py -v -r <race_id>
```

## Result example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/result.py -v -r <race_id>
```

## Primes example

```shell
PYTHONPATH=`pwd`/src python src/zpdatafetch/primes.py -v -r <race_id>
```
