"""Command-line interface for fetching Zwiftpower data.

This module provides a unified CLI for accessing all zpdatafetch
functionality including cyclist profiles, race results, signups,
team rosters, and prime data.
"""

import json
import sys
from typing import Any

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
  ZPCyclistFetch,
  ZPLeagueFetch,
  ZPPrimesFetch,
  ZPResultFetch,
  ZPSignupFetch,
  ZPSprintsFetch,
  ZPTeamFetch,
)
from zpdatafetch.logging_config import setup_logging


# ==============================================================================
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
    ZPCyclistFetch.set_sync_mode(True)
    ZPLeagueFetch.set_sync_mode(True)
    ZPPrimesFetch.set_sync_mode(True)
    ZPResultFetch.set_sync_mode(True)
    ZPSignupFetch.set_sync_mode(True)
    ZPSprintsFetch.set_sync_mode(True)
    ZPTeamFetch.set_sync_mode(True)

  # Handle --noaction flag (report what would be done without fetching)
  if args.noaction:
    format_noaction_output(args.cmd, args.id, args.raw)
    return None

  # Map command to class and fetch
  x: (
    ZPCyclistFetch
    | ZPLeagueFetch
    | ZPPrimesFetch
    | ZPResultFetch
    | ZPSignupFetch
    | ZPSprintsFetch
    | ZPTeamFetch
  )

  match args.cmd:
    case 'cyclist':
      x = ZPCyclistFetch()
    case 'league':
      x = ZPLeagueFetch()
    case 'primes':
      x = ZPPrimesFetch()
    case 'racelog':
      x = ZPCyclistFetch()
      try:
        x.fetch(*args.id)
      except Exception as e:
        # Import here to avoid circular dependency
        from shared.exceptions import NetworkError

        # Handle network errors with appropriate verbosity
        if isinstance(e, NetworkError):
          error_msg = str(e)
          # Extract Zwift ID from error message if present
          zwid = None
          if 'Failed to fetch Zwift ID' in error_msg:
            # Extract ID from message like "Failed to fetch Zwift ID 5348735"
            import re

            match = re.search(r'Zwift ID (\d+)', error_msg)
            if match:
              zwid = match.group(1)

          # Format output based on verbosity
          if args.debug:
            # Debug mode: re-raise to show full traceback
            raise
          if args.verbose:
            # Verbose mode: show HTTP status and URL
            lines = error_msg.split('\n')
            # Extract key parts
            first_line = lines[0] if lines else str(e)
            endpoint = next(
              (line for line in lines if 'Endpoint:' in line),
              None,
            )
            status = next(
              (line for line in lines if 'HTTP Status:' in line),
              None,
            )

            if zwid and endpoint:
              url = endpoint.split(': ', 1)[1] if ': ' in endpoint else 'unknown'
              # Extract status code and construct error message
              status_code = (
                status.split(': ')[1] if status and ': ' in status else '403'
              )
              print(
                f"Failed to fetch Zwift ID {zwid}: Client error '{status_code} Forbidden' for url '{url}'",
                file=sys.stderr,
              )
            else:
              print(first_line, file=sys.stderr)
              if endpoint:
                print(endpoint, file=sys.stderr)
          else:
            # Normal mode: simplified message with suggestion and profile link
            lines = error_msg.split('\n')
            suggestion = next(
              (line for line in lines if 'Suggestion:' in line),
              None,
            )
            if zwid and suggestion:
              print(
                f'Failed to fetch Zwift ID {zwid}: {suggestion.split(": ", 1)[1]} - https://zwiftpower.com/profile.php?z={zwid}',
                file=sys.stderr,
              )
            else:
              print(lines[0] if lines else str(e), file=sys.stderr)
          return 1
        # Non-network errors
        print(f'Error fetching data: {e}', file=sys.stderr)
        return 1

      # Extract racelog data
      racelogs: dict[int, Any] = {}
      for zwid_str in args.id:
        zwid = int(zwid_str)  # Convert string to int for racelog() call
        try:
          racelog = x.racelog(zwid)
          racelogs[zwid] = racelog
        except (ValueError, KeyError) as e:
          print(f'Error getting racelog for {zwid}: {e}', file=sys.stderr)
          return 1

      # Output racelog data based on flags
      if args.raw:
        # Output raw JSON strings from the fetched cyclist data
        for key, value in x._raw.items():
          print(f'{key}: {value}')
      elif args.json or args.v1fetch:
        # Output as JSON
        serializable = {
          key: value.aslist() if hasattr(value, 'aslist') else value
          for key, value in racelogs.items()
        }
        print(json.dumps(serializable, indent=2))
      elif args.excluded or args.extras:
        # Output excluded and/or extras fields from each race in racelogs
        for zwid, racelog in racelogs.items():
          print(f'{zwid}:')

          # Iterate through each race and show excluded/extras for that race
          for race in racelog:
            has_excluded = False
            has_extras = False

            # Output excluded fields if requested
            if args.excluded:
              if hasattr(race, 'excluded'):
                excluded_data = race.excluded()
                if excluded_data:
                  print(f'  {race!r}')
                  print(f'    excluded: {excluded_data}')
                  has_excluded = True

            # Output extras fields if requested
            if args.extras:
              if hasattr(race, 'extras'):
                extras_data = race.extras()
                if extras_data:
                  if not has_excluded:
                    print(f'  {race!r}')
                  print(f'    extras: {extras_data}')
                  has_extras = True
      else:
        # Default: output repr of each ZPRacelog
        for key, racelog in racelogs.items():
          print(f'{key}: {racelog!r}')
      return None
    case 'result':
      x = ZPResultFetch()
    case 'signup':
      x = ZPSignupFetch()
    case 'sprints':
      x = ZPSprintsFetch()
    case 'team':
      x = ZPTeamFetch()
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
  elif args.json or args.v1fetch:
    # Output as JSON (--json or legacy --v1fetch)
    # Convert objects to dicts for JSON serialization
    serializable = {
      key: value.asdict() if hasattr(value, 'asdict') else value
      for key, value in x._fetched.items()
    }
    print(json.dumps(serializable, indent=2))
  elif args.extras or args.excluded:
    # Output extras and/or excluded fields
    for key, value in x._fetched.items():
      print(f'{key}:')
      has_excluded = False
      has_extras = False

      # Output excluded fields if requested
      if args.excluded:
        # Check for excluded at the collection level
        if hasattr(value, 'excluded'):
          value_excluded = value.excluded()
          if value_excluded:
            print(f'  collection excluded: {value_excluded}')
            has_excluded = True

        # Check for excluded in each item if it's a collection
        if hasattr(value, '__iter__') and not isinstance(value, str):
          try:
            for item in value:  # type: ignore[iteration-not-supported]
              if hasattr(item, 'excluded'):
                item_excluded = item.excluded()
                if item_excluded:
                  print(f'  {item!r}')
                  print(f'    excluded: {item_excluded}')
                  has_excluded = True
          except (TypeError, AttributeError):
            pass

      # Output extras fields if requested
      if args.extras:
        # Check for extras at the collection level
        if hasattr(value, 'extras'):
          value_extras = value.extras()
          if value_extras:
            print(f'  collection extras: {value_extras}')
            has_extras = True

        # Check for extras in each item if it's a collection
        if hasattr(value, '__iter__') and not isinstance(value, str):
          try:
            for item in value:  # type: ignore[iteration-not-supported]
              if hasattr(item, 'extras'):
                item_extras = item.extras()
                if item_extras:
                  print(f'  {item!r}')
                  print(f'    extras: {item_extras}')
                  has_extras = True
          except (TypeError, AttributeError):
            pass

      # Show appropriate "no data" messages for each requested flag
      if args.excluded and not has_excluded:
        print('  No excluded')
      if args.extras and not has_extras:
        print('  No extras')
  else:
    # Default: output object repr, with special handling for nested collections
    def print_collection(obj: Any, indent: int = 0) -> None:  # noqa: ANN401
      """Recursively print collections with proper indentation.

      Handles nested collections like ZPPrime -> ZPPrimeSegment -> ZPPrimeResult.
      """
      prefix = '  ' * indent

      # Check if this is a collection (has __len__ and __iter__)
      if (
        hasattr(obj, '__len__')
        and hasattr(obj, '__iter__')
        and not isinstance(obj, str)
      ):
        print(f'{prefix}{obj!r}')
        # Iterate through items and show each recursively
        try:
          for item in obj:
            print_collection(item, indent + 1)
        except (TypeError, AttributeError):
          pass
      else:
        # Not a collection, just print repr
        print(f'{prefix}{obj!r}')

    for key, value in x._fetched.items():
      print(f'{key}:', end='')
      # Check if the value itself is a collection that needs recursive expansion
      if (
        hasattr(value, '__len__')
        and hasattr(value, '__iter__')
        and not isinstance(value, str)
      ):
        print()  # Newline after key for collections
        try:
          for item in value:  # type: ignore[iteration-not-supported]
            print_collection(item, indent=1)
        except (TypeError, AttributeError):
          pass
      else:
        # Not a collection, print on same line
        print(f' {value!r}')

  return None


# ==============================================================================
if __name__ == '__main__':
  sys.exit(main())
