default: ruff ty test

test *ARGS:
  OSTYPE=`uname` . .venv/bin/activate ; pytest {{ARGS}}

check: ruff ty

ruff:
  OSTYPE=`uname` . .venv/bin/activate ; ruff check src test

ty:
  OSTYPE=`uname` . .venv/bin/activate ; ty check src test

