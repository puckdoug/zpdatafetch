"""Command-line interface for fetching ZwiftRanking data.

This module provides a unified CLI for accessing zrdatafetch functionality
including rider ratings, race results, and team rosters.

The CLI matches the zpdata interface:
  zrdata rating <id>       Fetch rider rating
  zrdata result <id>       Fetch race results
  zrdata team <id>         Fetch team roster
"""

import logging
import sys
from argparse import ArgumentParser

from zrdatafetch.logging_config import setup_logging

# Note: Placeholder imports. These will be replaced with actual class imports
# once the refactored classes are implemented.
# from zrdatafetch import Config, ZRRating, ZRResult, ZRTeam


# ===============================================================================
def main() -> int | None:
  """Main entry point for the zrdatafetch CLI.

  Provides commands for:
    - rating: Fetch rider rating/ranking data by Zwift ID
    - result: Fetch race results by event ID
    - team: Fetch team/club roster data by team ID

  Returns:
    None on success, or exit code on error
  """
  desc = """
Module for fetching ZwiftRanking data using the ZwiftRanking API
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
    choices=('rating', 'result', 'team'),
  )
  p.add_argument(
    'id',
    help='the id to search for',
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

  # TODO: Implement command routing
  # x: ZRRating | ZRResult | ZRTeam
  #
  # match args.cmd:
  #   case 'rating':
  #     x = ZRRating()
  #   case 'result':
  #     x = ZRResult()
  #   case 'team':
  #     x = ZRTeam()
  #   case _:
  #     sys.exit(0)
  #
  # x.fetch(*args.id)
  #
  # if args.raw:
  #   print(x.raw)
  # else:
  #   print(x.json())

  return None


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
