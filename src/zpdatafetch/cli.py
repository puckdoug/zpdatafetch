"""Command-line interface for fetching Zwiftpower data.

This module provides a unified CLI for accessing all zpdatafetch
functionality including cyclist profiles, race results, signups,
team rosters, and prime data.
"""

import logging
import sys
from argparse import ArgumentParser

from zpdatafetch import Config, Cyclist, Primes, Result, Signup, Team
from zpdatafetch.logging_config import setup_logging


# ===============================================================================
def main() -> int | None:
  """Main entry point for the zpdatafetch CLI.

  Provides commands for:
    - config: Set up Zwiftpower credentials
    - cyclist: Fetch cyclist profile data by Zwift ID
    - primes: Fetch race prime/segment data by race ID
    - result: Fetch race results by race ID
    - signup: Fetch race signups by race ID
    - team: Fetch team roster data by team ID

  Returns:
    None on success, or exit code on error
  """
  desc = """
Module for fetching zwiftpower data using the Zwifpower API
  """
  p = ArgumentParser(description=desc)
  p.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='enable INFO level logging to console',
  )
  p.add_argument(
    '-vv',
    '--debug',
    action='store_true',
    help='enable DEBUG level logging to console',
  )
  p.add_argument(
    '--log-file',
    type=str,
    metavar='PATH',
    help='path to log file (enables file logging)',
  )
  p.add_argument(
    '-r',
    '--raw',
    action='store_true',
    help='print the raw results returned to screen',
  )
  p.add_argument(
    'cmd',
    help='which command to run',
    nargs='?',
    choices=('config', 'cyclist', 'primes', 'result', 'signup', 'team'),
  )
  p.add_argument(
    'id',
    help='the id to search for, ignored for config',
    nargs='*',
  )
  args = p.parse_args()

  # Configure logging based on arguments
  if args.debug:
    setup_logging(log_file=args.log_file, console_level=logging.DEBUG)
  elif args.verbose:
    setup_logging(log_file=args.log_file, console_level=logging.INFO)
  elif args.log_file:
    # File logging only, no console output
    setup_logging(log_file=args.log_file, force_console=False)
  # else: use default ERROR-only logging to stderr

  x: Cyclist | Primes | Result | Signup | Team

  match args.cmd:
    case 'config':
      c = Config()
      c.setup()
      sys.exit(0)
    case 'cyclist':
      x = Cyclist()
    case 'primes':
      x = Primes()
    case 'result':
      x = Result()
    case 'signup':
      x = Signup()
    case 'team':
      x = Team()
    case _:
      sys.exit(0)

  x.fetch(*args.id)

  if args.raw:
    print(x.raw)
  else:
    print(x.json())

  return None


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
