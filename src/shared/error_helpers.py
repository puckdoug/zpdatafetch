"""Error formatting utilities for consistent, informative error messages.

Provides helper functions to format network errors, authentication errors,
and other exceptions with consistent context (operation, endpoint, HTTP status,
retry information, and recovery suggestions).

This module ensures all error messages across zpdatafetch and zrdatafetch
follow a standardized multi-line format that includes:
- What operation failed
- Why it failed (reason)
- HTTP status code (where applicable)
- Which endpoint was being accessed
- Retry attempt information (where applicable)
- Actionable recovery suggestions
"""


def format_network_error(
  operation: str,
  endpoint: str,
  error: Exception,
  status_code: int | None = None,
  attempt: int | None = None,
  max_attempts: int | None = None,
) -> str:
  """Format a network error with operation context and recovery suggestions.

  Args:
    operation: What operation was being attempted (e.g., 'fetch rider data')
    endpoint: The URL being accessed
    error: The underlying exception
    status_code: HTTP status code (optional, e.g., 429, 500)
    attempt: Current attempt number (optional)
    max_attempts: Maximum number of attempts (optional)

  Returns:
    Formatted error message with multi-line context
  """
  lines = []
  lines.append(f'Failed to {operation}: {error!s}')
  lines.append(f'Endpoint: {endpoint}')

  if status_code is not None:
    lines.append(f'HTTP Status: {status_code}')

  if attempt is not None and max_attempts is not None:
    lines.append(f'Attempt: {attempt}/{max_attempts}')

  # Add recovery suggestion based on error type
  suggestion = _get_recovery_suggestion(error, status_code, endpoint)
  if suggestion:
    lines.append(f'Suggestion: {suggestion}')

  return '\n'.join(lines)


def format_auth_error(
  operation: str,
  endpoint: str,
  error: Exception,
  suggestion: str | None = None,
) -> str:
  """Format an authentication error with recovery suggestions.

  Args:
    operation: What operation was being attempted
    endpoint: The URL being accessed
    error: The underlying exception
    suggestion: Custom recovery suggestion (overrides auto-generated one)

  Returns:
    Formatted error message
  """
  lines = []
  lines.append(f'Failed to {operation}: {error!s}')
  lines.append(f'Endpoint: {endpoint}')

  if suggestion:
    lines.append(f'Suggestion: {suggestion}')
  else:
    lines.append(
      'Suggestion: Verify your credentials are correct and account is active.',
    )

  return '\n'.join(lines)


def format_json_error(
  endpoint: str,
  error: Exception,
  silent: bool = True,
) -> str | None:
  """Format a JSON decode error.

  Args:
    endpoint: The URL that was being parsed
    error: The JSON decode exception
    silent: If True, return None (silent failure mode)

  Returns:
    Formatted error message or None for silent failures
  """
  if silent:
    return None

  lines = []
  lines.append(f'Failed to parse response JSON from {endpoint}: {error!s}')
  lines.append(
    'Suggestion: The API response may be invalid or the format has changed.',
  )

  return '\n'.join(lines)


def _get_recovery_suggestion(
  error: Exception,
  status_code: int | None = None,
  endpoint: str | None = None,
) -> str:
  """Generate a recovery suggestion based on error type and HTTP status.

  Args:
    error: The exception
    status_code: HTTP status code if available
    endpoint: The endpoint URL being accessed (optional)

  Returns:
    Recovery suggestion message
  """
  if status_code:
    if status_code == 429:
      return 'Rate limit exceeded. Wait before retrying the request.'
    if status_code == 403:
      # Special case for cyclist profile 403 errors
      if endpoint and 'zwiftpower.com/cache3/profile/' in endpoint:
        return 'Check that this is a valid rider Zwift ID.'
      return 'Authentication failed. Verify your credentials and API access.'
    if status_code == 401:
      return 'Authentication failed. Verify your credentials and API access.'
    if status_code == 404:
      return 'Resource not found. Verify the endpoint URL is correct.'
    if 500 <= status_code < 600:
      return (
        'Server error. The API may be temporarily unavailable. '
        'Retry after a moment.'
      )

  error_str = str(error).lower()
  if 'connection' in error_str or 'refused' in error_str:
    return 'Check your network connection and verify the API is accessible.'
  if 'timeout' in error_str:
    return 'The request timed out. Check your network connection or try again.'
  if 'ssl' in error_str or 'certificate' in error_str:
    return (
      'SSL certificate verification failed. Check your system certificates.'
    )

  return 'Verify your network connection and try again.'
