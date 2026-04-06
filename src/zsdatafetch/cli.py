"""Command-line interface for fetching Zwift Status data.

This module provides a unified CLI for accessing zsdatafetch functionality
including service status, incidents, and scheduled maintenance.

The CLI:
  zsdata status                  Overall status summary
  zsdata status --components     Component list only
  zsdata incidents               All incidents
  zsdata incidents --unresolved  Unresolved incidents only
  zsdata maintenance             All scheduled maintenance
  zsdata maintenance --upcoming  Upcoming maintenance only
  zsdata maintenance --active    Active maintenance only
"""

import json
import sys
from argparse import ArgumentParser
from typing import Any

from shared.cli import (
  configure_logging_from_args,
  get_package_version,
  validate_command_name,
  validate_command_provided,
)
from zsdatafetch import (
  ZSIncidentFetch,
  ZSMaintenanceFetch,
  ZSSummaryFetch,
)
from zsdatafetch.logging_config import setup_logging
from zsdatafetch.models.summary import ZSSummary


def _create_parser() -> ArgumentParser:
  """Create argument parser for zsdata CLI.

  Builds a custom parser instead of using create_base_parser
  because zsdata does not use v1fetch, extras, excluded, or
  positional IDs.

  Returns:
    Configured ArgumentParser
  """
  p = ArgumentParser(
    description=(
      'Fetch Zwift service status data from the '
      'Statuspage API'
    ),
  )

  p.add_argument(
    '--version',
    action='version',
    version=f'%(prog)s {get_package_version("zpdatafetch")}',
  )

  # Logging
  p.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='enable verbose output (INFO level logging)',
  )
  p.add_argument(
    '-vv', '--debug',
    action='store_true',
    help='enable debug output (DEBUG level logging)',
  )
  p.add_argument(
    '--log-file',
    type=str,
    metavar='PATH',
    help='write logging output to file',
  )

  # Output format
  p.add_argument(
    '-r', '--raw',
    action='store_true',
    help='print raw JSON as received from the server',
  )
  p.add_argument(
    '--json',
    action='store_true',
    help='output fetched data as JSON',
  )

  # Dry-run
  p.add_argument(
    '--noaction',
    action='store_true',
    help=(
      'show what would be done without actually '
      'fetching data'
    ),
  )

  # Sync mode
  p.add_argument(
    '--sync',
    action='store_true',
    help='use synchronous (non-parallel) requests',
  )

  # zsdata-specific arguments
  p.add_argument(
    '--components',
    action='store_true',
    help='show components only (status command)',
  )
  p.add_argument(
    '--unresolved',
    action='store_true',
    help='show unresolved only (incidents command)',
  )
  p.add_argument(
    '--upcoming',
    action='store_true',
    help='show upcoming only (maintenance command)',
  )
  p.add_argument(
    '--active',
    action='store_true',
    help='show active only (maintenance command)',
  )

  # Command
  p.add_argument(
    'cmd',
    nargs='?',
    metavar='CMD',
    help=(
      'command to execute: '
      '{status,incidents,maintenance}'
    ),
  )

  return p


def main() -> int | None:
  """Main entry point for the zsdatafetch CLI.

  Returns:
    None on success, or exit code on error
  """
  p = _create_parser()
  args = p.parse_intermixed_args()
  configure_logging_from_args(args, setup_logging)

  # Handle sync mode
  if args.sync:
    ZSSummaryFetch.set_sync_mode(True)
    ZSIncidentFetch.set_sync_mode(True)
    ZSMaintenanceFetch.set_sync_mode(True)

  if not validate_command_provided(args.cmd, p):
    return None

  if args.cmd == 'help':
    p.print_help()
    return None

  match args.cmd:
    case 'status':
      if args.noaction:
        variant = (
          'components' if args.components else 'summary'
        )
        print(f'Would fetch status {variant} data')
        return None

      try:
        fetcher = ZSSummaryFetch()
        result = fetcher.fetch(
          components_only=args.components,
        )
        _output_summary(args, result, fetcher)
      except Exception as e:
        print(f'Error fetching status: {e}', file=sys.stderr)
        return 1

    case 'incidents':
      if args.noaction:
        variant = (
          'unresolved' if args.unresolved else 'all'
        )
        print(f'Would fetch {variant} incidents')
        return None

      try:
        fetcher = ZSIncidentFetch()
        result = fetcher.fetch(
          unresolved_only=args.unresolved,
        )
        _output_list(args, result, fetcher)
      except Exception as e:
        print(
          f'Error fetching incidents: {e}',
          file=sys.stderr,
        )
        return 1

    case 'maintenance':
      if args.noaction:
        if args.upcoming:
          variant = 'upcoming'
        elif args.active:
          variant = 'active'
        else:
          variant = 'all'
        print(f'Would fetch {variant} maintenance')
        return None

      try:
        fetcher = ZSMaintenanceFetch()
        result = fetcher.fetch(
          upcoming=args.upcoming,
          active=args.active,
        )
        _output_list(args, result, fetcher)
      except Exception as e:
        print(
          f'Error fetching maintenance: {e}',
          file=sys.stderr,
        )
        return 1

    case _:
      if not validate_command_name(
        args.cmd,
        ('status', 'incidents', 'maintenance'),
      ):
        return 1

  return None


def _output_summary(
  args: Any,  # noqa: ANN401
  summary: ZSSummary,
  fetcher: ZSSummaryFetch,
) -> None:
  """Output summary results in the requested format.

  Args:
    args: Parsed CLI arguments
    summary: ZSSummary object
    fetcher: ZSSummaryFetch instance (for raw output)
  """
  if args.raw:
    print(fetcher.raw())
  elif args.json:
    print(json.dumps(summary.asdict(), indent=2))
  else:
    _print_summary_repr(summary)


def _output_list(
  args: Any,  # noqa: ANN401
  items: list[Any],  # noqa: ANN401
  fetcher: ZSIncidentFetch | ZSMaintenanceFetch,
) -> None:
  """Output list results in the requested format.

  Args:
    args: Parsed CLI arguments
    items: List of dataclass objects
    fetcher: Fetcher instance (for raw output)
  """
  if args.raw:
    print(fetcher.raw())
  elif args.json:
    serializable = [
      item.asdict() for item in items
    ]
    print(json.dumps(serializable, indent=2))
  else:
    if not items:
      print('No results')
    else:
      for item in items:
        print(repr(item))


def _print_summary_repr(summary: ZSSummary) -> None:
  """Print a human-readable summary representation.

  Args:
    summary: ZSSummary to display
  """
  print(
    f'Status: {summary.status.description} '
    f'({summary.status.indicator})',
  )
  print(f'Page: {summary.page.name}')

  if summary.components:
    print(f'Components ({len(summary.components)}):')
    for comp in summary.components:
      if not comp.group:
        print(f'  {comp.name}: {comp.status}')

  if summary.incidents:
    print(f'Incidents ({len(summary.incidents)}):')
    for inc in summary.incidents:
      print(f'  {inc.name} ({inc.status}) - {inc.impact}')

  if summary.scheduled_maintenances:
    count = len(summary.scheduled_maintenances)
    print(f'Scheduled Maintenance ({count}):')
    for m in summary.scheduled_maintenances:
      print(
        f'  {m.name} ({m.status}) '
        f'{m.scheduled_for} - {m.scheduled_until}',
      )


if __name__ == '__main__':
  exit_code = main()
  if exit_code is not None:
    sys.exit(exit_code)
