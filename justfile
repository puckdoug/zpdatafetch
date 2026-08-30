# all syntax
default:
  @just --list

# Run pytest
test *ARGS:
  OSTYPE=`uname` . .venv/bin/activate ; pytest {{ ARGS }}

# Runs tests which hit live API endpoints
test-live *ARGS:
  OSTYPE=`uname` . .venv/bin/activate ;  pytest --live test/live {{ ARGS }}

# Runs live tests and regular local/fast tests together
test-all *ARGS:
  test {{ ARGS }}
  test-live {{ ARGS }}

# run ruff and ty lints
check: ruff ty

# ruff lints across src and test
ruff:
  OSTYPE=`uname` . .venv/bin/activate ; ruff check src test

# type checking across src and test
ty:
  OSTYPE=`uname` . .venv/bin/activate ; ty check src test
