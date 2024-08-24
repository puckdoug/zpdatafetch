# zpdatafetch

A python library and command-line tool for fetching data from zwiftpower.

## Installation

```sh
pip install zpdatafetch
```

## Usage

zpdatafetch comes with a command-line tool named zpdata. This can be used to fetch data directly from zwiftpower. It sends the json response to stdout. It also acts as a guide for how to use the library in your own program.

For both command-line and library usage, you will need to have a zwiftpower account. You will need set up your credentials in your system keyring. This can be done using the following commands from they python keyring library (installed as part of zpdatafetch if not already available on your system):

```sh
keyring set zpdatafetch username
keyring set zpdatafetch password
```

In principle, the library can use alternate backend keyrings, but this is not tested so far. At the moment, only the system keyring is used. See [the keyring docs](https://keyring.readthedocs.io/en/latest/) for more details on how to use the keyring and keyring library for your system.

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
c.fetch(1234567) # fetch data for cyclist with zwift id 1234567
print(c.json())
```

The interface for each of the objects is effectively the same as the example above, with the individual class and id number changed as appropriate. The available classes are as follows:

- Cyclist: fetch one or more cyclists by zwift id
- Primes: fetch primes from one or more races using event id
- Result: fetch results from one or more races (finish, points) using event id
- Signup: fetch signups for a particular event by event id
- Team: fetch team data by team id

The classes ZP class is the main driver for the library. It is used to fetch the data from zwiftpower. The other classes are used to parse the data into a more useful format.

### Object signature

Each object has a common set of methods available:

```python
obj.fetch(id) or obj.fetch([id1, id2, id3]) # fetch the data from zwiftpower. As argument, fetch expects a single ID or a list (tuple or array) of IDs.
obj.json() # return the data as a json object
obj.asdict() # return the data as a dictionary
print(obj) # effectively the same as obj.asdict()
```

In addition, the object can be set to work in verbose mode, which it will pass to the ZP object which drives the interaction with the website, by simply setting:

```python
obj.verbose = True
```

## Development

I've switched over to using [https://astral.sh/](Astral)'s [https://astral.sh/uv/](uv) for the development toolchain.
It's technically experimental still (as of the time of this writing) but at the rate they move it may not be by the time
you read this. Directions below try to cover both options.

1. Install this package
2. Install the requirements

```sh
pip install -r requirements.txt
```
or
```sh
uv sync
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
or
```sh
  uv run zp.py
```


This should return a '200' message if you've set everything up correctly, proving that the program can
log in correctly to Zwiftpower.

With a few exceptions, each object has a callable interface that can be used for simple direct access
to experiment without additional code wrapped around it - yours or the provided command-line tool. They each respond to the -h flag to provide help. Basic examples follow.

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

While useful and usable, there's a bit that can be done to improve this package. Anyone interested to
contribute is welcome to do so. These are the areas where I could use help:

- [ ] Add more tests and improve coverage
- [ ] Improve github actions setup
- [ ] Improve error handling
- [ ] Check if there are any objects not handled
- [ ] Update the interface to allow alternate keyrings
- [ ] Sort out cases where zpdata isn't properly installed as executable
