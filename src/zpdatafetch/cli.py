"""Command-line interface for fetching Zwiftpower data.

This module provides a unified CLI for accessing all zpdatafetch
functionality including cyclist profiles, race results, signups,
team rosters, and prime data.
"""

import logging
import sys
from argparse import ArgumentParser

from zpdatafetch import Config, Cyclist, Primes, Result, Signup, Sprints, Team
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
    - sprints: Fetch race sprint data by race ID
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
    action='count',
    default=0,
    help='increase output verbosity (-v for INFO, -vv for DEBUG)',
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
    '--noaction',
    action='store_true',
    help='report what would be done without actually fetching data',
  )
  p.add_argument(
    'cmd',
    nargs='?',
    metavar='{config,cyclist,primes,result,signup,sprints,team}',
    help='which command to run',
  )
  p.add_argument(
    'id',
    nargs='*',
    help='ID(s) to search for',
  )

  # Use parse_intermixed_args to handle flags after positional arguments
  # This allows: zpdata cyclist --noaction 123 456
  args = p.parse_intermixed_args()

  # Configure logging based on arguments (output to stderr)
  if args.verbose >= 2:
    setup_logging(
      log_file=args.log_file, console_level=logging.DEBUG, force_console=True
    )
  elif args.verbose == 1:
    setup_logging(
      log_file=args.log_file, console_level=logging.INFO, force_console=True
    )
  elif args.log_file:
    # File logging only, no console output
    setup_logging(log_file=args.log_file, force_console=False)
  # else: use default ERROR-only logging to stderr

  # Handle commands
  if not args.cmd:
    p.print_help()
    return None

  if args.cmd == 'config':
    c = Config()
    c.setup()
    return None

  # For non-config commands, validate we have a valid command
  valid_commands = ('cyclist', 'primes', 'result', 'signup', 'sprints', 'team')
  if args.cmd not in valid_commands:
    # The 'cmd' might actually be an ID if user didn't provide a command
    print(f'Error: invalid command "{args.cmd}"')
    print(f'Valid commands: {", ".join(valid_commands)}')
    return 1

  # For non-config commands, we need an ID
  if not args.id:
    print(f'Error: {args.cmd} command requires at least one ID')
    return 1

  # Handle --noaction flag (report what would be done without fetching)
  if args.noaction:
    print(f'Would fetch {args.cmd} data for: {", ".join(args.id)}')
    if args.raw:
      print('(raw output format)')
    return None

  # Map command to class and fetch
  x: Cyclist | Primes | Result | Signup | Sprints | Team

  match args.cmd:
    case 'cyclist':
      x = Cyclist()
    case 'primes':
      x = Primes()
    case 'result':
      x = Result()
    case 'signup':
      x = Signup()
    case 'sprints':
      x = Sprints()
    case 'team':
      x = Team()
    case _:
      print(f'Unknown command: {args.cmd}')
      return 1

  x.fetch(*args.id)

  if args.raw:
    print(x.raw)
  else:
    print(x.json())

  return None


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
