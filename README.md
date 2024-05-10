# zp_data

A python library for fetching data from zwiftpower

## installation

1. Install this package
2. Install the requirements

```sh
pip install -r requirements.txt
```

3. Set up your keyring. You may want to use a separate account on zwiftpower for this.

```sh
keyring set zp_data username
keyring set zp_data password
```

4. Run the downloader

```sh
  PYTHONPATH=`pwd`/src python src/zp_data/zp.py
```

## Cyclist example

```shell
PYTHONPATH=`pwd`/src python src/zp_data/cyclist.py -v -r <zwift_id>
```

## Team example

```shell
PYTHONPATH=`pwd`/src python src/zp_data/team.py -v -r <team_id>
```

## Signup example

```shell
PYTHONPATH=`pwd`/src python src/zp_data/signup.py -v -r <race_id>
```

## Result example

```shell
PYTHONPATH=`pwd`/src python src/zp_data/result.py -v -r <race_id>
```

## Primes example

```shell
PYTHONPATH=`pwd`/src python src/zp_data/primes.py -v -r <race_id>
```
