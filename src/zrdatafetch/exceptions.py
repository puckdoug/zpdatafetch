"""Custom exceptions for zrdatafetch module.

Provides typed exceptions for different error conditions when interacting
with the Zwiftracing API.
"""


# ===============================================================================
class ZRAuthenticationError(Exception):
  """Raised when authentication with Zwiftracing API fails.

  This exception is raised when API credentials are rejected, missing,
  or authentication otherwise fails.
  """


# ===============================================================================
class ZRNetworkError(Exception):
  """Raised when network requests to Zwiftracing API fail.

  This exception is raised for HTTP errors, connection errors, timeouts,
  and other network-related issues.
  """


# ===============================================================================
class ZRConfigError(Exception):
  """Raised when configuration is invalid or missing.

  This exception is raised when credentials are not found, invalid,
  or other configuration issues are detected.
  """
