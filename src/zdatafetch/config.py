"""Configuration management for Zwift API credentials.

Handles storage and retrieval of Zwift username and password using the
system keyring for secure credential management.
"""

import sys
from getpass import getpass
from typing import Any

import keyring

from shared.config import BaseConfig
from zdatafetch.logging_config import get_logger

logger = get_logger(__name__)


class Config(BaseConfig):
  """Zwift API configuration manager.

  Manages Zwift credentials using system keyring for secure storage.
  Credentials are used to authenticate with Zwift's unofficial API.

  Attributes:
    username: Zwift username
    password: Zwift password
  """

  _service_name = 'zdatafetch'
  _username_key = 'username'
  _password_key = 'password'

  username: str = ''
  password: str = ''

  # ----------------------------------------------------------------------------
  def _get_domain(self) -> str:
    """Return the keyring domain for Zwift credentials.

    Returns:
      Domain name 'zdatafetch'
    """
    return 'zdatafetch'

  # ----------------------------------------------------------------------------
  def _prompt_for_credentials(self, **kwargs: Any) -> None:  # noqa: ANN401
    """Prompt for Zwift username and password.

    Args:
      username: Zwift username (prompts if empty)
      password: Zwift password (prompts securely if empty)
    """
    username = kwargs.get('username', '')
    password = kwargs.get('password', '')

    if username:
      self.username = username
      logger.debug('Using provided username')
    else:
      self.username = input('Zwift username (for use with zdatafetch): ')
      logger.debug('Username entered interactively')
      keyring.set_password(self.domain, 'username', self.username)

    if password:
      self.password = password
      logger.debug('Using provided password')
    else:
      self.password = getpass(
        'Zwift password (for use with zdatafetch): ',
      )
      logger.debug('Password entered interactively')
      keyring.set_password(self.domain, 'password', self.password)

  # ----------------------------------------------------------------------------
  def _clear_credentials_impl(self) -> None:
    """Clear username and password from memory."""
    if self.username:
      self.username = '*' * len(self.username)
      self.username = ''
    if self.password:
      self.password = '*' * len(self.password)
      self.password = ''

  # ----------------------------------------------------------------------------
  def _verify_exists_impl(self) -> bool:
    """Check if username and password are set.

    Returns:
      True if both username and password are set, False otherwise
    """
    return bool(self.username and self.password)

  # ----------------------------------------------------------------------------
  def save(self) -> None:
    """Save current credentials to the system keyring.

    Stores both username and password under the configured domain.
    """
    logger.debug(f'Saving credentials to keyring domain: {self.domain}')
    keyring.set_password(self.domain, 'username', self.username)
    keyring.set_password(self.domain, 'password', self.password)
    logger.info('Credentials saved successfully')

  # ----------------------------------------------------------------------------
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


def main() -> None:
  """CLI entry point for config management."""
  c = Config()
  c.load()
  if c.verify_credentials_exist():
    print('Credentials are configured in keyring')
  else:
    print('No credentials found in keyring')


if __name__ == '__main__':
  sys.exit(main())
