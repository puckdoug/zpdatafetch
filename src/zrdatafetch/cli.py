"""Command-line interface for fetching Zwiftracing data.

This module provides a unified CLI for accessing zrdatafetch functionality
including rider ratings, race results, and team rosters.

The CLI matches the zpdata interface:
  zrdata rider <id>        Fetch rider rating
  zrdata result <id>       Fetch race results
  zrdata team <id>         Fetch team roster
"""

import sys

from shared.cli import (
  configure_logging_from_args,
  create_base_parser,
  format_noaction_output,
  handle_config_command,
  read_ids_from_file,
  validate_command_name,
  validate_command_provided,
  validate_ids_provided,
)
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

  # Create parser with common arguments
  p = create_base_parser(
    description=desc,
    command_metavar='{config,rider,result,team}',
  )

  # Add zrdatafetch-specific arguments
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

  # Use parse_intermixed_args to handle flags after positional arguments
  # This allows: zrdata rider --noaction 12345 67890
  args = p.parse_intermixed_args()

  # Configure logging based on arguments
  configure_logging_from_args(args, setup_logging)

  # Set premium tier mode if requested
  if args.premium:
    ZR_obj.set_premium_mode(True)

  # Handle no command
  if not validate_command_provided(args.cmd, p):
    return None

  # Route to appropriate command
  match args.cmd:
    case 'config':
      handle_config_command(Config, check_first=True)
      return None
    case 'rider':
      # Handle batch file input
      if args.batch_file:
        ids = read_ids_from_file(args.batch_file)
        if ids is None:
          return 1
        args.id = ids

      if not validate_ids_provided(args.id, 'rider'):
        return 1

      if args.noaction:
        if args.batch or args.batch_file:
          print(f'Would fetch {len(args.id)} riders using batch POST')
        else:
          format_noaction_output('rider', args.id, args.raw)
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
      if not validate_ids_provided(args.id, 'result'):
        return 1

      if args.noaction:
        format_noaction_output('result', args.id, args.raw)
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
      if not validate_ids_provided(args.id, 'team'):
        return 1

      if args.noaction:
        format_noaction_output('team', args.id, args.raw)
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
      if not validate_command_name(args.cmd, ('rider', 'result', 'team')):
        return 1

  return None


# ===============================================================================
if __name__ == '__main__':
  exit_code = main()
  if exit_code is not None:
    sys.exit(exit_code)
