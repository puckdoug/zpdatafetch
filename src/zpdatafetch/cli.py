"""Command-line interface for fetching Zwiftpower data.

This module provides a unified CLI for accessing all zpdatafetch
functionality including cyclist profiles, race results, signups,
team rosters, and prime data.
"""

import json
import sys

from shared.cli import (
  configure_logging_from_args,
  create_base_parser,
  format_noaction_output,
  handle_config_command,
  validate_command_name,
  validate_command_provided,
  validate_ids_provided,
)
from zpdatafetch import (
  Config,
  Cyclist,
  League,
  Primes,
  Result,
  Signup,
  Sprints,
  Team,
)
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
    - league: Fetch league standing data by league ID

  Returns:
    None on success, or exit code on error
  """
  desc = """
Module for fetching zwiftpower data using the Zwifpower API
  """

  # Create parser with common arguments
  p = create_base_parser(
    description=desc,
    command_metavar='{config,cyclist,league,primes,result,signup,sprints,team}',
  )

  # Use parse_intermixed_args to handle flags after positional arguments
  # This allows: zpdata cyclist --noaction 123 456
  args = p.parse_intermixed_args()

  # Configure logging based on arguments
  configure_logging_from_args(args, setup_logging)

  # Handle missing command
  if not validate_command_provided(args.cmd, p):
    return None

  # Handle config command
  if args.cmd == 'config':
    handle_config_command(Config, check_first=False)
    return None

  # For non-config commands, validate command name
  valid_commands = (
    'cyclist',
    'league',
    'primes',
    'result',
    'signup',
    'sprints',
    'team',
  )
  if not validate_command_name(args.cmd, valid_commands):
    return 1

  # For non-config commands, validate we have IDs
  if not validate_ids_provided(args.id, args.cmd):
    return 1

  # Handle --noaction flag (report what would be done without fetching)
  if args.noaction:
    format_noaction_output(args.cmd, args.id, args.raw)
    return None

  # Map command to class and fetch
  x: Cyclist | League | Primes | Result | Signup | Sprints | Team

  match args.cmd:
    case 'cyclist':
      x = Cyclist()
    case 'league':
      x = League()
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
    print(json.dumps(x.processed, indent=2))

  return None


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
