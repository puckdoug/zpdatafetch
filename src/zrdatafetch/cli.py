"""Command-line interface for fetching Zwiftracing data.

This module provides a unified CLI for accessing zrdatafetch functionality
including rider ratings, race results, and team rosters.

The CLI matches the zpdata interface:
  zrdata rider <id>        Fetch rider rating
  zrdata result <id>       Fetch race results
  zrdata team <id>         Fetch team roster
"""

import logging
import sys
from argparse import ArgumentParser

from zrdatafetch import Config, ZRResult, ZRRider, ZRTeam
from zrdatafetch.logging_config import setup_logging
from zrdatafetch.zr import ZR_obj


# ===============================================================================
def main() -> int | None:
  """Main entry point for the zrdatafetch CLI.

  Provides commands for:
    - rider: Fetch rider rating/ranking data by Zwift ID
    - result: Fetch race results by event ID
    - team: Fetch team/club roster data by team ID

  Returns:
    None on success, or exit code on error
  """
  desc = """
Module for fetching Zwiftracing data using the Zwiftracing API
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
    '--noaction',
    action='store_true',
    help='report what would be done without actually fetching data',
  )
  p.add_argument(
    '--batch',
    action='store_true',
    help='use batch POST endpoint for multiple IDs (rider command only)',
  )
  p.add_argument(
    '--batch-file',
    type=str,
    metavar='FILE',
    help='read IDs from file (one per line) for batch request (rider command only)',
  )
  p.add_argument(
    '--premium',
    action='store_true',
    help='use premium tier rate limits (higher request quotas)',
  )
  p.add_argument(
    'cmd',
    nargs='?',
    metavar='{config,rider,result,team}',
    help='which command to run',
  )
  p.add_argument(
    'id',
    nargs='*',
    help='ID(s) to search for',
  )

  # Use parse_intermixed_args to handle flags after positional arguments
  # This allows: zrdata rider --noaction 12345 67890
  args = p.parse_intermixed_args()

  # Configure logging based on arguments
  if args.debug:
    setup_logging(log_file=args.log_file, console_level=logging.DEBUG)
  elif args.verbose:
    setup_logging(log_file=args.log_file, console_level=logging.INFO)
  elif args.log_file:
    # File logging only, no console output
    setup_logging(log_file=args.log_file, force_console=False)
  # else: use default ERROR-only logging to stderr

  # Set premium tier mode if requested
  if args.premium:
    ZR_obj.set_premium_mode(True)

  # Handle no command
  if not args.cmd:
    p.print_help()
    return None

  # Route to appropriate command
  match args.cmd:
    case 'config':
      c = Config()
      c.load()
      if c.verify_credentials_exist():
        print('Authorization is already configured in keyring')
      else:
        c.setup()
        print('Authorization configured successfully')
      return None
    case 'rider':
      # Handle batch file input
      if args.batch_file:
        try:
          with open(args.batch_file) as f:
            args.id = [line.strip() for line in f if line.strip()]
        except OSError as e:
          print(f'Error reading batch file: {e}')
          return 1

      if not args.id:
        print('Error: rider command requires at least one ID')
        return 1

      if args.noaction:
        if args.batch or args.batch_file:
          print(f'Would fetch {len(args.id)} riders using batch POST')
        else:
          print(f'Would fetch rider data for: {", ".join(args.id)}')
        if args.raw:
          print('(raw output format)')
        return None

      # Handle batch request
      if args.batch or args.batch_file:
        try:
          # Convert IDs to integers for batch fetch
          rider_ids = [int(rid) for rid in args.id]
          riders = ZRRider.fetch_batch(*rider_ids)
          for zwift_id, rider in riders.items():
            if args.raw:
              print(rider.to_dict())
            else:
              print(rider.json())
        except ValueError as e:
          print(f'Error: Invalid Zwift ID in batch: {e}')
          return 1
        except Exception as e:
          print(f'Error fetching batch: {e}')
          return 1
      else:
        # Fetch and display rider data individually
        for zwift_id in args.id:
          try:
            rider = ZRRider(zwift_id=int(zwift_id))
            rider.fetch()
            if args.raw:
              print(rider.to_dict())
            else:
              print(rider.json())
          except ValueError:
            print(f'Error: Invalid Zwift ID: {zwift_id}')
            return 1
          except Exception as e:
            print(f'Error fetching rider {zwift_id}: {e}')
            return 1
    case 'result':
      if not args.id:
        print('Error: result command requires at least one ID')
        return 1

      if args.noaction:
        print(f'Would fetch result data for: {", ".join(args.id)}')
        if args.raw:
          print('(raw output format)')
        return None

      # Fetch and display result data
      for race_id in args.id:
        try:
          result = ZRResult(race_id=int(race_id))
          result.fetch()
          if args.raw:
            print(result.to_dict())
          else:
            print(result.json())
        except ValueError:
          print(f'Error: Invalid race ID: {race_id}')
          return 1
        except Exception as e:
          print(f'Error fetching result {race_id}: {e}')
          return 1
    case 'team':
      if not args.id:
        print('Error: team command requires at least one ID')
        return 1

      if args.noaction:
        print(f'Would fetch team data for: {", ".join(args.id)}')
        if args.raw:
          print('(raw output format)')
        return None

      # Fetch and display team data
      for team_id in args.id:
        try:
          team = ZRTeam(team_id=int(team_id))
          team.fetch()
          if args.raw:
            print(team.to_dict())
          else:
            print(team.json())
        except ValueError:
          print(f'Error: Invalid team ID: {team_id}')
          return 1
        except Exception as e:
          print(f'Error fetching team {team_id}: {e}')
          return 1
    case _:
      # Invalid command
      print(f'Error: invalid command "{args.cmd}"')
      print('Valid commands: config, rider, result, team')
      return 1

  return None


# ===============================================================================
if __name__ == '__main__':
  exit_code = main()
  if exit_code is not None:
    sys.exit(exit_code)
