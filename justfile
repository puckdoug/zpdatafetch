default: ruff ty pytest

pytest *ARGS:
  OSTYPE=`uname` . .venv/bin/activate ; pytest {{ARGS}}

ruff:
  OSTYPE=`uname` . .venv/bin/activate ; ruff check src test

ty:
  OSTYPE=`uname` . .venv/bin/activate ; ty check src test

