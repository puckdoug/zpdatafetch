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
    command_metavar='{config,cyclist,league,primes,racelog,result,signup,sprints,team}',
  )

  # Use parse_intermixed_args to handle flags after positional arguments
  # This allows: zpdata cyclist --noaction 123 456
  args = p.parse_intermixed_args()

  # Configure logging based on arguments
  configure_logging_from_args(args, setup_logging)

  # Handle missing command
  if not validate_command_provided(args.cmd, p):
    return None

  # Handle help command
  if args.cmd == 'help':
    p.print_help()
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
    'racelog',
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

  # Handle --sync flag (enable synchronous mode)
  if args.sync:
    Cyclist.set_sync_mode(True)
    League.set_sync_mode(True)
    Primes.set_sync_mode(True)
    Result.set_sync_mode(True)
    Signup.set_sync_mode(True)
    Sprints.set_sync_mode(True)
    Team.set_sync_mode(True)

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
    case 'racelog':
      x = Cyclist()
      x.fetch(*args.id)
      # Extract racelog data and convert to serializable format
      racelog_data = {}
      for zwid_str in args.id:
        zwid = int(zwid_str)  # Convert string to int for racelog() call
        try:
          racelog = x.racelog(zwid)
          racelog_data[zwid] = racelog.aslist()
        except (ValueError, KeyError) as e:
          print(f'Error getting racelog for {zwid}: {e}', file=sys.stderr)
          return 1

      # Output racelog data
      if args.raw:
        if len(racelog_data) == 1:
          print(json.dumps(list(racelog_data.values())[0], indent=2))
        else:
          for key, value in racelog_data.items():
            print(f'{key}: {json.dumps(value, indent=2)}')
      else:
        print(json.dumps(racelog_data, indent=2))
      return None
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
    # Output raw response text
    if len(x._raw) == 1:
      # Single ID: print just the raw string
      print(list(x._raw.values())[0])
    else:
      # Multiple IDs: print as key: value pairs (one per line)
      for key, value in x._raw.items():
        print(f'{key}: {value}')
  elif args.v1fetch:
    print(json.dumps(x._fetched, indent=2))
  else:
    print(json.dumps(x._fetched, indent=2))

  return None


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
