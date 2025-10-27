"""Configuration management for zrdatafetch.

Manages Zwiftracing API authorization credentials using the system keyring
for secure storage.
"""

import sys
from getpass import getpass
from typing import Any

import keyring

from zrdatafetch.logging_config import get_logger

logger = get_logger(__name__)


# ===============================================================================
class Config:
  """Manages Zwiftracing API credentials using system keyring.

  Stores and retrieves the authorization header from the system keyring
  service, providing secure credential management for the zrdatafetch
  library.

  Attributes:
    domain: Keyring service name (default: 'zrdatafetch')
    authorization: Zwiftracing API authorization header value
    kr: Reference to the active keyring backend
  """

  domain: str = 'zrdatafetch'
  authorization: str = ''
  _test_domain_override: str | None = None  # Class variable for test domain override

  # -----------------------------------------------------------------------
  def __init__(self) -> None:
    """Initialize Config and set up keyring access.

    Uses test domain override if set (for testing), otherwise uses
    default 'zrdatafetch' domain.
    """
    self.kr: Any = keyring.get_keyring()
    logger.debug(f'Using keyring backend: {type(self.kr).__name__}')

    # Use test domain if set
    if Config._test_domain_override:
      self.domain = Config._test_domain_override
      logger.debug(f'Using test domain override: {self.domain}')
    else:
      logger.debug(f'Using default domain: {self.domain}')

  # -----------------------------------------------------------------------
  def set_keyring(self, kr: Any) -> None:
    """Set a custom keyring backend.

    Args:
      kr: Keyring backend instance (e.g., PlaintextKeyring for testing)
    """
    logger.debug(f'Setting custom keyring backend: {type(kr).__name__}')
    keyring.set_keyring(kr)

  # -----------------------------------------------------------------------
  def replace_domain(self, domain: str) -> None:
    """Change the keyring service domain.

    Args:
      domain: New domain name to use for keyring operations
    """
    logger.debug(f'Changing domain from {self.domain} to {domain}')
    self.domain = domain

  # -----------------------------------------------------------------------
  def save(self) -> None:
    """Save authorization header to the system keyring.

    Stores the authorization header value under the configured domain.
    """
    logger.debug(f'Saving authorization to keyring domain: {self.domain}')
    keyring.set_password(self.domain, 'authorization', self.authorization)
    logger.info('Authorization saved successfully')

  # -----------------------------------------------------------------------
  def load(self) -> None:
    """Load authorization header from the system keyring.

    Retrieves authorization header from the configured domain.
    Updates instance attribute if authorization is found.
    """
    logger.debug(f'Loading authorization from keyring domain: {self.domain}')
    auth = keyring.get_password(self.domain, 'authorization')
    if auth:
      self.authorization = auth
      logger.debug('Authorization loaded from keyring')
    else:
      logger.debug('No authorization found in keyring')

  # -----------------------------------------------------------------------
  def setup(self, authorization: str = '') -> None:
    """Configure Zwiftracing API authorization interactively or programmatically.

    If authorization is not provided, prompts the user interactively.
    Saves authorization to keyring after collection.

    Args:
      authorization: Zwiftracing API authorization header (prompts if empty)
    """
    logger.info('Setting up Zwiftracing authorization')

    if authorization:
      self.authorization = authorization
      logger.debug('Using provided authorization')
    else:
      self.authorization = getpass(
        'Zwiftracing API authorization header (for use with zrdatafetch): ',
      )
      logger.debug('Authorization entered interactively')

    keyring.set_password(self.domain, 'authorization', self.authorization)
    logger.info('Authorization setup completed')

  # -----------------------------------------------------------------------
  def clear_credentials(self) -> None:
    """Securely clear credentials from memory.

    Overwrites authorization with placeholder values before clearing.
    This reduces the risk of credential recovery from memory dumps.

    SECURITY NOTE:
      Python strings are immutable, so this provides best-effort protection.
      For applications requiring higher security, use dedicated processes with
      memory protection or containers with appropriate isolation.
    """
    logger.debug('Clearing authorization from memory')
    if self.authorization:
      self.authorization = '*' * len(self.authorization)
      self.authorization = ''
    logger.debug('Authorization cleared from memory')

  # -----------------------------------------------------------------------
  def verify_credentials_exist(self) -> bool:
    """Verify that authorization is configured in keyring.

    Checks if authorization is present without exposing it.
    This is a safer alternative to dump() for credential verification.

    Returns:
      True if authorization is set, False otherwise
    """
    logger.debug('Checking if authorization exists in keyring')
    return bool(self.authorization)


# ===============================================================================
def main() -> None:
  """CLI entry point for config management."""
  c = Config()
  c.load()
  if c.verify_credentials_exist():
    print('Authorization is configured in keyring')
  else:
    print('No authorization found in keyring')


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
