import logging
import sys
from getpass import getpass
from typing import Any, Optional

import keyring

from zpdatafetch.logging_config import get_logger

logger = get_logger(__name__)

# ===============================================================================


class Config:
  """Manages Zwiftpower credentials using system keyring.

  Stores and retrieves username and password from the system keyring
  service, providing secure credential management for the zpdatafetch
  library.

  Attributes:
    verbose: Enable verbose output for debugging
    domain: Keyring service name (default: 'zpdatafetch')
    username: Zwiftpower username
    password: Zwiftpower password
    kr: Reference to the active keyring backend
  """

  domain: str = 'zpdatafetch'
  username: str = ''
  password: str = ''
  _test_domain_override: str | None = None  # Class variable for test domain override

  # -----------------------------------------------------------------------------
  def __init__(self) -> None:
    """Initialize Config and set up keyring access.

    Uses test domain override if set (for testing), otherwise uses
    default 'zpdatafetch' domain.
    """
    self.kr: Any = keyring.get_keyring()
    logger.debug(f'Using keyring backend: {type(self.kr).__name__}')

    # Use test domain if set
    if Config._test_domain_override:
      self.domain = Config._test_domain_override
      logger.debug(f'Using test domain override: {self.domain}')
    else:
      logger.debug(f'Using default domain: {self.domain}')

  #   self.load()

  # -----------------------------------------------------------------------------
  def set_keyring(self, kr: Any) -> None:
    """Set a custom keyring backend.

    Args:
      kr: Keyring backend instance (e.g., PlaintextKeyring for testing)
    """
    logger.debug(f'Setting custom keyring backend: {type(kr).__name__}')
    keyring.set_keyring(kr)

  # -----------------------------------------------------------------------------
  def replace_domain(self, domain: str) -> None:
    """Change the keyring service domain.

    Args:
      domain: New domain name to use for keyring operations
    """
    logger.debug(f'Changing domain from {self.domain} to {domain}')
    self.domain = domain

  # -----------------------------------------------------------------------------
  def save(self) -> None:
    """Save current credentials to the system keyring.

    Stores both username and password under the configured domain.
    """
    logger.debug(f'Saving credentials to keyring domain: {self.domain}')
    keyring.set_password(self.domain, 'username', self.username)
    keyring.set_password(self.domain, 'password', self.password)
    logger.info('Credentials saved successfully')

  # -----------------------------------------------------------------------------
  def load(self) -> None:
    """Load credentials from the system keyring.

    Retrieves username and password from the configured domain.
    Updates instance attributes if credentials are found.
    """
    logger.debug(f'Loading credentials from keyring domain: {self.domain}')
    u = keyring.get_password(self.domain, 'username')
    if u:
      self.username = u
      logger.debug('Username loaded from keyring')
    else:
      logger.debug('No username found in keyring')

    p = keyring.get_password(self.domain, 'password')
    if p:
      self.password = p
      logger.debug('Password loaded from keyring')
    else:
      logger.debug('No password found in keyring')

  # -----------------------------------------------------------------------------
  def setup(self, username: str = '', password: str = '') -> None:
    """Configure Zwiftpower credentials interactively or programmatically.

    If username/password are not provided, prompts the user interactively.
    Saves credentials to keyring after collection.

    Args:
      username: Zwiftpower username (prompts if empty)
      password: Zwiftpower password (prompts securely if empty)
    """
    logger.info('Setting up Zwiftpower credentials')

    if username:
      self.username = username
      logger.debug('Using provided username')
    else:
      self.username = input('zwiftpower username (for use with zpdatafetch): ')
      logger.debug('Username entered interactively')
      keyring.set_password(self.domain, 'username', self.username)

    if password:
      self.password = password
      logger.debug('Using provided password')
    else:
      self.password = getpass(
        'zwiftpower password (for use with zpdatafetch): ',
      )
      logger.debug('Password entered interactively')
      keyring.set_password(self.domain, 'password', self.password)

    logger.info('Credentials setup completed')

  # -----------------------------------------------------------------------------
  def dump(self) -> None:
    """Print current credentials to stdout.

    Warning: This exposes the password in plaintext. Use only for debugging.
    """
    print(f'username: {self.username}')
    print(f'password: {self.password}')


# ===============================================================================
def main() -> None:
  c = Config()
  c.dump()


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
