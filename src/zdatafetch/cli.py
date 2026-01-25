"""Command-line interface for fetching Zwift data.

This module provides a unified CLI for accessing Zwift's unofficial API
functionality including rider profiles, followers, and RideOns.
"""

import sys
from argparse import ArgumentParser

from shared.cli import (
  configure_logging_from_args,
  format_noaction_output,
  handle_config_command,
  validate_command_name,
  validate_command_provided,
  validate_ids_provided,
)
from shared.exceptions import ConfigError, NetworkError
from zdatafetch import Config, ZwiftProfile
from zdatafetch.activity import ZwiftActivity
from zdatafetch.followers import ZwiftFollowers
from zdatafetch.logging_config import get_logger, setup_logging
from zdatafetch.rideons import ZwiftRideOns
from zdatafetch.ridersinworld import ZwiftRidersInWorld
from zdatafetch.worlds import ZwiftWorlds

logger = get_logger(__name__)


def main() -> int | None:
  """Main entry point for the zdatafetch CLI.

  Provides commands for:
      - config: Set up Zwift credentials
      - profile: Fetch rider profile data by Zwift ID
      - followers: Fetch follower data (not yet implemented)
      - rideons: Fetch RideOn data (not yet implemented)

  Returns:
      None on success, or exit code on error
  """
  desc = """
Fetch data from Zwift's unofficial API

Commands:
  config          Configure Zwift credentials
  profile         Fetch rider profile data
  followers       Fetch follower/followee data
  rideons         Fetch RideOn data or give RideOns
  activity        Fetch activity history
  worlds          Fetch active worlds
  ridersinworld   Fetch riders in a specific world
  """

  # Create parser (custom for zdatafetch, no --v1fetch)
  p = ArgumentParser(description=desc)

  # Logging arguments
  p.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='enable verbose output (INFO level logging)',
  )
  p.add_argument(
    '-vv',
    '--debug',
    action='store_true',
    help='enable debug output (DEBUG level logging)',
  )
  p.add_argument(
    '--log-file',
    type=str,
    metavar='PATH',
    help='write logging output to file',
  )

  # Output format arguments
  p.add_argument(
    '-r',
    '--raw',
    action='store_true',
    help='print raw result data as received from the server',
  )

  # Dry-run argument
  p.add_argument(
    '--noaction',
    action='store_true',
    help='show what would be done without actually fetching data',
  )

  # Sync mode argument
  p.add_argument(
    '--sync',
    action='store_true',
    help='use synchronous (non-parallel) requests',
  )

  # Followers-specific arguments
  p.add_argument(
    '--followers-only',
    action='store_true',
    help='fetch only followers, not followees (followers command only)',
  )
  p.add_argument(
    '--followees-only',
    action='store_true',
    help='fetch only followees, not followers (followers command only)',
  )

  # RideOns-specific arguments
  p.add_argument(
    '--give',
    action='store_true',
    help='give a RideOn instead of fetching (rideons command only)',
  )

  # Activity-specific arguments
  p.add_argument(
    '--start',
    type=int,
    default=0,
    help='starting activity ID for pagination (activity command only, default: 0)',
  )
  p.add_argument(
    '--limit',
    type=int,
    default=20,
    help='number of activities to fetch (activity command only, default: 20)',
  )

  # RidersInWorld-specific arguments
  p.add_argument(
    '--world',
    type=str,
    help='world name or ID for ridersinworld command (e.g., watopia, london, 1, 3)',
  )

  # Commands
  p.add_argument(
    'cmd',
    nargs='?',
    metavar='CMD',
    help='command to execute: {config,profile,followers,rideons,activity,worlds,ridersinworld}',
  )

  # IDs for commands
  p.add_argument(
    'id',
    nargs='*',
    help='ID(s) for the command',
  )

  # Parse arguments
  args = p.parse_intermixed_args()

  # Configure logging
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

  # Validate command name
  valid_commands = (
    'profile',
    'followers',
    'rideons',
    'activity',
    'worlds',
    'ridersinworld',
  )
  if not validate_command_name(args.cmd, valid_commands):
    return 1

  # Validate we have IDs (except for worlds command which takes no IDs)
  if args.cmd != 'worlds' and not validate_ids_provided(args.id, args.cmd):
    return 1

  # Handle --noaction flag
  if args.noaction:
    format_noaction_output(args.cmd, args.id, args.raw)
    return None

  # Execute command
  try:
    match args.cmd:
      case 'profile':
        # Convert IDs to integers
        rider_ids = [int(id_str) for id_str in args.id]

        if len(rider_ids) == 1:
          # Single profile
          profile = ZwiftProfile()
          profile.fetch(rider_ids[0])

          if args.raw:
            print(profile.raw())
          else:
            print(profile)
        else:
          # Multiple profiles - return as dictionary
          profiles = ZwiftProfile.fetch_multiple(*rider_ids)

          if args.raw:
            # Raw: print each ID and raw data
            for rider_id, profile in profiles.items():
              print(f'{rider_id}: {profile.raw()}')
          else:
            # Normal: print dictionary format
            print('{')
            for rider_id, profile in profiles.items():
              # Indent the profile output
              profile_str = str(profile)
              indented = '\n'.join(
                f'  {line}' for line in profile_str.split('\n')
              )
              print(f'  {rider_id}: {indented.lstrip()},')
            print('}')

      case 'followers':
        # Convert IDs to integers
        rider_ids = [int(id_str) for id_str in args.id]

        # Determine what to fetch
        include_followers = not args.followees_only
        include_followees = not args.followers_only

        if len(rider_ids) == 1:
          # Single rider
          followers = ZwiftFollowers()
          followers.fetch(
            rider_ids[0],
            include_followers=include_followers,
            include_followees=include_followees,
          )

          if args.raw:
            print(followers.raw())
          else:
            print(followers)
        else:
          # Multiple riders
          followers_data = ZwiftFollowers.fetch_multiple(
            *rider_ids,
            include_followers=include_followers,
            include_followees=include_followees,
          )

          if args.raw:
            # Raw: print each ID and raw data
            for rider_id, followers in followers_data.items():
              print(f'{rider_id}: {followers.raw()}')
          else:
            # Normal: print dictionary format
            print('{')
            for rider_id, followers in followers_data.items():
              followers_str = str(followers)
              indented = '\n'.join(
                f'  {line}' for line in followers_str.split('\n')
              )
              print(f'  {rider_id}: {indented.lstrip()},')
            print('}')

      case 'rideons':
        # RideOns requires rider_id and activity_id
        if args.give:
          # Give RideOn: needs exactly 2 IDs (rider_id, activity_id)
          if len(args.id) != 2:
            print(
              'Error: --give requires exactly 2 arguments: rider_id activity_id',
              file=sys.stderr,
            )
            return 1

          rider_id = int(args.id[0])
          activity_id = int(args.id[1])

          success = ZwiftRideOns.give_rideon(rider_id, activity_id)
          if success:
            print(f'Successfully gave RideOn to activity {activity_id}')
          else:
            print(
              f'Failed to give RideOn to activity {activity_id}',
              file=sys.stderr,
            )
            return 1
        else:
          # Fetch RideOns: needs pairs of IDs (rider_id, activity_id)
          if len(args.id) % 2 != 0:
            print(
              'Error: rideons command requires pairs of IDs: rider_id activity_id',
              file=sys.stderr,
            )
            return 1

          # Parse pairs
          activity_tuples = []
          for i in range(0, len(args.id), 2):
            rider_id = int(args.id[i])
            activity_id = int(args.id[i + 1])
            activity_tuples.append((rider_id, activity_id))

          if len(activity_tuples) == 1:
            # Single activity
            rideons = ZwiftRideOns()
            rideons.fetch(activity_tuples[0][0], activity_tuples[0][1])

            if args.raw:
              print(rideons.raw())
            else:
              print(rideons)
          else:
            # Multiple activities
            rideons_data = ZwiftRideOns.fetch_multiple(*activity_tuples)

            if args.raw:
              # Raw: print each key and raw data
              for key, rideons in rideons_data.items():
                print(f'{key}: {rideons.raw()}')
            else:
              # Normal: print dictionary format
              print('{')
              for key, rideons in rideons_data.items():
                rideons_str = str(rideons)
                indented = '\n'.join(
                  f'  {line}' for line in rideons_str.split('\n')
                )
                print(f'  {key}: {indented.lstrip()},')
              print('}')

      case 'activity':
        # Convert IDs to integers
        rider_ids = [int(id_str) for id_str in args.id]

        if len(rider_ids) == 1:
          # Single rider
          activity = ZwiftActivity()
          activity.fetch(rider_ids[0], start=args.start, limit=args.limit)

          if args.raw:
            print(activity.raw())
          else:
            print(activity)
        else:
          # Multiple riders
          activities = ZwiftActivity.fetch_multiple(
            *rider_ids,
            start=args.start,
            limit=args.limit,
          )

          if args.raw:
            # Raw: print each ID and raw data
            for rider_id, activity in activities.items():
              print(f'{rider_id}: {activity.raw()}')
          else:
            # Normal: print dictionary format
            print('{')
            for rider_id, activity in activities.items():
              activity_str = str(activity)
              indented = '\n'.join(
                f'  {line}' for line in activity_str.split('\n')
              )
              print(f'  {rider_id}: {indented.lstrip()},')
            print('}')

      case 'worlds':
        # Worlds command takes no IDs
        worlds = ZwiftWorlds()
        worlds.fetch()

        if args.raw:
          print(worlds.raw())
        else:
          print(worlds)

      case 'ridersinworld':
        # RidersInWorld can use --world flag or ID/name as argument
        if args.world:
          # Use --world flag
          try:
            # Try as world ID first
            world_id = int(args.world)
            riders = ZwiftRidersInWorld()
            riders.fetch(world_id)
          except ValueError:
            # Not a number, try as world name
            riders = ZwiftRidersInWorld()
            riders.fetch_by_name(args.world)

          if args.raw:
            print(riders.raw())
          else:
            print(riders)
        else:
          # Use IDs/names from arguments - try to parse as int, fall back to name
          world_ids = []
          for id_str in args.id:
            try:
              world_ids.append(int(id_str))
            except ValueError:
              # Not a number, try as world name
              from zdatafetch.worlds import get_world_id

              world_id = get_world_id(id_str)
              if world_id is None:
                print(
                  f'Error: Unknown world name or invalid ID: {id_str}',
                  file=sys.stderr,
                )
                return 1
              world_ids.append(world_id)

          if len(world_ids) == 1:
            # Single world
            riders = ZwiftRidersInWorld()
            riders.fetch(world_ids[0])

            if args.raw:
              print(riders.raw())
            else:
              print(riders)
          else:
            # Multiple worlds
            riders_data = ZwiftRidersInWorld.fetch_multiple(*world_ids)

            if args.raw:
              # Raw: print each world ID and raw data
              for world_id, riders in riders_data.items():
                print(f'{world_id}: {riders.raw()}')
            else:
              # Normal: print dictionary format
              print('{')
              for world_id, riders in riders_data.items():
                riders_str = str(riders)
                indented = '\n'.join(
                  f'  {line}' for line in riders_str.split('\n')
                )
                print(f'  {world_id}: {indented.lstrip()},')
              print('}')

    return None

  except ConfigError as e:
    print(f'Configuration error: {e}', file=sys.stderr)
    return 1
  except NetworkError as e:
    print(f'Network error: {e}', file=sys.stderr)
    return 1
  except Exception as e:
    logger.exception('Unexpected error')
    print(f'Error: {e}', file=sys.stderr)
    return 1


if __name__ == '__main__':
  sys.exit(main())
