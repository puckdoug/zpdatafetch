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
from shared.exceptions import NetworkError
from zdatafetch import Config, ZwiftAuth, ZwiftProfile
from zdatafetch.followers import ZwiftFollowers
from zdatafetch.logging_config import get_logger, setup_logging
from zdatafetch.rideons import ZwiftRideOns

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
  config      Configure Zwift credentials
  profile     Fetch rider profile data
  followers   Fetch follower/followee data (not yet implemented)
  rideons     Fetch RideOn data (not yet implemented)
  """

  # Create parser (custom for zdatafetch, no --v1fetch)
  p = ArgumentParser(description=desc)

  # Logging arguments
  p.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="enable verbose output (INFO level logging)",
  )
  p.add_argument(
    "-vv",
    "--debug",
    action="store_true",
    help="enable debug output (DEBUG level logging)",
  )
  p.add_argument(
    "--log-file",
    type=str,
    metavar="PATH",
    help="write logging output to file",
  )

  # Output format arguments
  p.add_argument(
    "-r",
    "--raw",
    action="store_true",
    help="print raw result data as received from the server",
  )

  # Dry-run argument
  p.add_argument(
    "--noaction",
    action="store_true",
    help="show what would be done without actually fetching data",
  )

  # Sync mode argument
  p.add_argument(
    "--sync",
    action="store_true",
    help="use synchronous (non-parallel) requests",
  )

  # Commands
  p.add_argument(
    "cmd",
    nargs="?",
    metavar="CMD",
    help="command to execute: {config,profile,followers,rideons}",
  )

  # IDs for commands
  p.add_argument(
    "id",
    nargs="*",
    help="ID(s) for the command",
  )

  # Parse arguments
  args = p.parse_intermixed_args()

  # Configure logging
  configure_logging_from_args(args, setup_logging)

  # Handle missing command
  if not validate_command_provided(args.cmd, p):
    return None

  # Handle config command
  if args.cmd == "config":
    handle_config_command(Config, check_first=False)
    return None

  # Validate command name
  valid_commands = ("profile", "followers", "rideons")
  if not validate_command_name(args.cmd, valid_commands):
    return 1

  # Validate we have IDs
  if not validate_ids_provided(args.id, args.cmd):
    return 1

  # Handle --noaction flag
  if args.noaction:
    format_noaction_output(args.cmd, args.id, args.raw)
    return None

  # Execute command
  try:
    match args.cmd:
      case "profile":
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
              print(f"{rider_id}: {profile.raw()}")
          else:
            # Normal: print dictionary format
            print("{")
            for rider_id, profile in profiles.items():
              # Indent the profile output
              profile_str = str(profile)
              indented = "\n".join(f"  {line}" for line in profile_str.split("\n"))
              print(f"  {rider_id}: {indented.lstrip()},")
            print("}")

      case "followers":
        # Load credentials for followers (still uses old pattern)
        config = Config()
        config.load()
        if not config.username or not config.password:
          print(
            'Error: Zwift credentials not found. Run "zdata config" to set up credentials.',
            file=sys.stderr,
          )
          return 1
        auth = ZwiftAuth(config.username, config.password)
        auth.login()
        fetcher = ZwiftFollowers(auth)
        fetcher.fetch(*[int(id_str) for id_str in args.id])

      case "rideons":
        # Load credentials for rideons (still uses old pattern)
        config = Config()
        config.load()
        if not config.username or not config.password:
          print(
            'Error: Zwift credentials not found. Run "zdata config" to set up credentials.',
            file=sys.stderr,
          )
          return 1
        auth = ZwiftAuth(config.username, config.password)
        auth.login()
        fetcher = ZwiftRideOns(auth)
        fetcher.fetch(*[int(id_str) for id_str in args.id])

    return None

  except NotImplementedError as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1
  except NetworkError as e:
    print(f"Network error: {e}", file=sys.stderr)
    return 1
  except Exception as e:
    logger.exception("Unexpected error")
    print(f"Error: {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
  sys.exit(main())
