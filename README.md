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
keyring set zwiftpower username
keyring set zwiftpower password
```

4. Run the downloader

```sh
  PYTHONPATH=`pwd`/src python src/zp_data/zp.py
```

## More to come
