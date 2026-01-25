"""Command-line interface for fetching Zwiftracing data.

This module provides a unified CLI for accessing zrdatafetch functionality
including rider ratings, race results, and team rosters.

The CLI matches the zpdata interface:
  zrdata rider <id>        Fetch rider rating
  zrdata result <id>       Fetch race results
  zrdata team <id>         Fetch team roster
"""

import json
import sys
from typing import Any

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
from zrdatafetch import (
  Config,
  ZRResultFetch,
  ZRRiderFetch,
  ZRTeamFetch,
)
from zrdatafetch.logging_config import setup_logging
from zrdatafetch.zr import ZR_obj


# ==============================================================================
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
    help=(
      'read IDs from file (one per line) for batch request (rider command only)'
    ),
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

  # Handle --sync flag (enable synchronous mode)
  if args.sync:
    ZRRiderFetch.set_sync_mode(True)
    ZRResultFetch.set_sync_mode(True)
    ZRTeamFetch.set_sync_mode(True)

  # Handle no command
  if not validate_command_provided(args.cmd, p):
    return None

  # Handle help command
  if args.cmd == 'help':
    p.print_help()
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

      try:
        # Convert IDs to integers
        rider_ids = [int(rid) for rid in args.id]

        # Handle batch request
        if args.batch or args.batch_file:
          riders = ZRRiderFetch.fetch_batch(*rider_ids)
          fetcher = None  # Batch doesn't use fetcher instance
        else:
          fetcher = ZRRiderFetch()
          riders = fetcher.fetch(*rider_ids)

        # Output results
        _output_results(args, riders, fetcher)

      except ValueError as e:
        print(f'Error: Invalid Zwift ID: {e}')
        return 1
      except Exception as e:
        print(f'Error fetching rider: {e}')
        return 1

    case 'result':
      if not validate_ids_provided(args.id, 'result'):
        return 1

      if args.noaction:
        format_noaction_output('result', args.id, args.raw)
        return None

      try:
        # Convert IDs to integers
        race_ids = [int(rid) for rid in args.id]
        fetcher = ZRResultFetch()
        results = fetcher.fetch(*race_ids)

        # Output results
        _output_results(args, results, fetcher)

      except ValueError as e:
        print(f'Error: Invalid race ID: {e}')
        return 1
      except Exception as e:
        print(f'Error fetching result: {e}')
        return 1

    case 'team':
      if not validate_ids_provided(args.id, 'team'):
        return 1

      if args.noaction:
        format_noaction_output('team', args.id, args.raw)
        return None

      try:
        # Convert IDs to integers
        team_ids = [int(tid) for tid in args.id]
        fetcher = ZRTeamFetch()
        teams = fetcher.fetch(*team_ids)

        # Output results
        _output_results(args, teams, fetcher)

      except ValueError as e:
        print(f'Error: Invalid team ID: {e}')
        return 1
      except Exception as e:
        print(f'Error fetching team: {e}')
        return 1

    case _:
      # Invalid command
      if not validate_command_name(args.cmd, ('rider', 'result', 'team')):
        return 1

  return None


def _output_results(
  args: Any,  # noqa: ANN401
  fetched: dict[int, Any],
  fetcher: ZRRiderFetch | ZRResultFetch | ZRTeamFetch | None,
) -> None:
  """Output results in the requested format.

  Args:
    args: Parsed command-line arguments
    fetched: Dictionary of fetched objects (id -> dataclass)
    fetcher: Fetcher instance (or None for batch requests)
  """
  if args.raw:
    # Output raw response text
    if fetcher is None:
      # Batch mode: serialize objects back to JSON
      if len(fetched) == 1:
        print(json.dumps(list(fetched.values())[0].asdict(), indent=2))
      else:
        for key, value in fetched.items():
          print(f'{key}: {json.dumps(value.asdict(), indent=2)}')
    else:
      # Regular mode: use stored raw JSON
      raw_dict = fetcher.raw()
      if len(fetched) == 1:
        print(list(raw_dict.values())[0])
      else:
        for key, value in raw_dict.items():
          print(f'{key}: {value}')
  elif args.json or args.v1fetch:
    # Output as JSON (--json or legacy --v1fetch)
    # Convert objects to dicts for JSON serialization
    serializable = {
      key: value.asdict() if hasattr(value, 'asdict') else value
      for key, value in fetched.items()
    }
    print(json.dumps(serializable, indent=2))
  elif args.extras or args.excluded:
    # Output extras and/or excluded fields
    for key, value in fetched.items():
      print(f'{key}:')
      has_excluded = False
      has_extras = False

      # Output excluded fields if requested
      if args.excluded:
        # Check for excluded at the object level
        if hasattr(value, 'excluded'):
          value_excluded = value.excluded()
          if value_excluded:
            print(f'  object excluded: {value_excluded}')
            has_excluded = True

        # Check for excluded in each item if it's a collection
        if hasattr(value, '__iter__') and not isinstance(value, str):
          try:
            for item in value:
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
        # Check for extras at the object level
        if hasattr(value, 'extras'):
          value_extras = value.extras()
          if value_extras:
            print(f'  object extras: {value_extras}')
            has_extras = True

        # Check for extras in each item if it's a collection
        if hasattr(value, '__iter__') and not isinstance(value, str):
          try:
            for item in value:
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

      Handles nested collections like ZRRaceResult -> ZRRiderResult or
      ZRTeamRoster -> ZRTeamMember.
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

    for key, value in fetched.items():
      print(f'{key}:', end='')
      # Check if the value itself is a collection that needs recursive expansion
      if (
        hasattr(value, '__len__')
        and hasattr(value, '__iter__')
        and not isinstance(value, str)
      ):
        print()  # Newline after key for collections
        try:
          for item in value:
            print_collection(item, indent=1)
        except (TypeError, AttributeError):
          pass
      else:
        # Single object, print on same line
        print(f' {value!r}')


# ==============================================================================
if __name__ == '__main__':
  exit_code = main()
  if exit_code is not None:
    sys.exit(exit_code)
