"""Shared exceptions for Zwift data fetching packages.

Provides a common set of exception types for error handling across
both zpdatafetch and zrdatafetch packages.
"""


# ==============================================================================
class FetchError(Exception):
  """Base exception for fetch-related errors.

  This is the base class for all exceptions raised during data fetching
  operations. Subclass this for specific error conditions.
  """


# ==============================================================================
class AuthenticationError(FetchError):
  """Raised when authentication fails.

  This exception is raised when API credentials are rejected, missing,
  or authentication otherwise fails. This applies to both Zwiftpower
  (username/password) and Zwiftracing (authorization token) APIs.
  """


# ==============================================================================
class NetworkError(FetchError):
  """Raised when network requests fail.

  This exception is raised for HTTP errors, connection errors, timeouts,
  and other network-related issues when communicating with the APIs.
  """


# ==============================================================================
class ConfigError(FetchError):
  """Raised when configuration is invalid or missing.

  This exception is raised when credentials are not found in the keyring,
  configuration files are invalid, or other configuration issues are
  detected.
  """
