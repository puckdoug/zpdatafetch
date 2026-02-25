default: ruff ty pytest

pytest:
  OSTYPE=`uname` . .venv/bin/activate ; pytest

ruff:
  OSTYPE=`uname` . .venv/bin/activate ; ruff check src test

ty:
  OSTYPE=`uname` . .venv/bin/activate ; ty check src test

