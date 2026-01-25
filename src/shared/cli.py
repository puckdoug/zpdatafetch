"""Shared CLI utilities for Zwift data fetching packages.

Provides common command-line argument parsing, validation, and logging setup
functionality for both zpdatafetch and zrdatafetch CLIs.
"""

import logging
from argparse import ArgumentParser, Namespace
from collections.abc import Callable


def create_base_parser(
  description: str,
  command_metavar: str,
) -> ArgumentParser:
  """Create argument parser with common CLI arguments.

  Args:
    description: CLI description text
    command_metavar: Metavar for command choices (e.g., '{config,rider,result}')

  Returns:
    ArgumentParser configured with common arguments for both packages.
    Caller can add package-specific arguments after this call.
  """
  parser = ArgumentParser(description=description)

  # Logging arguments
  parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='enable verbose output (INFO level logging)',
  )
  parser.add_argument(
    '-vv',
    '--debug',
    action='store_true',
    help='enable debug output (DEBUG level logging)',
  )
  parser.add_argument(
    '--log-file',
    type=str,
    metavar='PATH',
    help='write logging output to file',
  )

  # Output format arguments
  parser.add_argument(
    '-r',
    '--raw',
    action='store_true',
    help='print raw result data as received from the server',
  )
  parser.add_argument(
    '--json',
    action='store_true',
    help='output fetched data as JSON (default: object repr)',
  )
  parser.add_argument(
    '--extras',
    action='store_true',
    help='report recently added fields not handled natively',
  )
  parser.add_argument(
    '--excluded',
    action='store_true',
    help='report recognized fields not yet explicitly handled',
  )
  parser.add_argument(
    '--v1fetch',
    action='store_true',
    help='output fetched data in v1.8 format (for backward compatibility)',
  )

  # Dry-run argument
  parser.add_argument(
    '--noaction',
    action='store_true',
    help='show what would be done without actually fetching data',
  )

  # Sync mode argument
  parser.add_argument(
    '--sync',
    action='store_true',
    help='use synchronous (non-parallel) requests',
  )

  # Commands
  parser.add_argument(
    'cmd',
    nargs='?',
    metavar='CMD',
    help=f'command to execute: {command_metavar}',
  )

  # IDs
  parser.add_argument(
    'id',
    nargs='*',
    help='ID(s) for the command',
  )

  return parser


def configure_logging_from_args(
  args: Namespace,
  setup_logging_func: Callable,
) -> None:
  """Configure logging based on parsed CLI arguments.

  Uses dependency injection to support package-specific logging setup functions.

  Args:
    args: Parsed arguments from ArgumentParser
    setup_logging_func: Package-specific setup_logging function to call
  """
  if args.debug:
    setup_logging_func(
      log_file=args.log_file,
      console_level=logging.DEBUG,
      force_console=True,
    )
  elif args.verbose:
    setup_logging_func(
      log_file=args.log_file,
      console_level=logging.INFO,
      force_console=True,
    )
  elif args.log_file:
    setup_logging_func(log_file=args.log_file, force_console=False)


def handle_config_command(
  config_class: type,
  check_first: bool = False,
) -> None:
  """Handle config command with optional credential checking.

  Args:
    config_class: Config class to instantiate (ZPConfig or ZRConfig)
    check_first: If True, check existing credentials before prompting
                 (zrdatafetch style). If False, always prompt for new
                 credentials (zpdatafetch style).
  """
  c = config_class()

  if check_first:
    c.load()
    if c.verify_credentials_exist():
      print('Authorization is already configured in keyring')
    else:
      c.setup()
      print('Authorization configured successfully')
  else:
    c.setup()


def validate_command_provided(
  cmd: str | None,
  parser: ArgumentParser,
) -> bool:
  """Check if command was provided.

  Args:
    cmd: Command string or None
    parser: ArgumentParser to print help if needed

  Returns:
    True if command provided, False otherwise.
  """
  if cmd is None:
    parser.print_help()
    return False
  return True


def validate_command_name(
  cmd: str,
  valid_commands: tuple[str, ...],
) -> bool:
  """Validate command is in list of valid commands.

  Args:
    cmd: Command to validate
    valid_commands: Tuple of valid command names

  Returns:
    True if valid, False if invalid.
  """
  if cmd not in valid_commands:
    print(f'Error: Unknown command "{cmd}"')
    return False
  return True


def validate_ids_provided(
  ids: list[str],
  cmd: str,
) -> bool:
  """Check if IDs were provided for command.

  Args:
    ids: List of ID strings
    cmd: Command name (for error message)

  Returns:
    True if IDs provided, False otherwise.
  """
  if not ids:
    print(f'Error: {cmd} command requires one or more IDs')
    return False
  return True


def format_noaction_output(
  cmd: str,
  ids: list[str],
  raw: bool,
) -> None:
  """Print standardized noaction (dry-run) output.

  Args:
    cmd: Command name
    ids: List of IDs that would be fetched
    raw: Whether raw format would be used
  """
  id_str = ', '.join(ids)
  print(f'Would fetch {cmd} data for: {id_str}')
  if raw:
    print('(raw output format)')


def read_ids_from_file(filepath: str) -> list[str] | None:
  """Read IDs from file, filtering blank lines.

  Args:
    filepath: Path to file containing IDs (one per line)

  Returns:
    List of ID strings, or None if error occurs.
  """
  try:
    with open(filepath) as f:
      return [line.strip() for line in f if line.strip()]
  except OSError as e:
    print(f'Error reading batch file: {e}')
    return None
