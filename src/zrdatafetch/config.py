"""Configuration management for zrdatafetch.

Manages Zwiftracing API authorization credentials using the system keyring
for secure storage.
"""

import sys
from getpass import getpass
from typing import Any

import keyring

from shared.config import BaseConfig
from zrdatafetch.logging_config import get_logger

logger = get_logger(__name__)


# ==============================================================================
class ZRConfig(BaseConfig):
  """Manages Zwiftracing API credentials using system keyring.

  Stores and retrieves the authorization header from the system keyring
  service, providing secure credential management for the zrdatafetch
  library.

  Attributes:
    authorization: Zwiftracing API authorization header value
  """

  authorization: str = ''

  # ----------------------------------------------------------------------------
  def _get_domain(self) -> str:
    """Return the keyring domain for Zwiftracing credentials.

    Returns:
      Domain name 'zrdatafetch'
    """
    return 'zrdatafetch'

  # ----------------------------------------------------------------------------
  def _prompt_for_credentials(self, **kwargs: Any) -> None:  # noqa: ANN401
    """Prompt for Zwiftracing API authorization header.

    Args:
      authorization: Zwiftracing API authorization header (prompts if empty)
    """
    authorization = kwargs.get('authorization', '')

    if authorization:
      self.authorization = authorization
      logger.debug('Using provided authorization')
    else:
      self.authorization = getpass(
        'Zwiftracing API authorization header (for use with zrdatafetch): ',
      )
      logger.debug('Authorization entered interactively')

    keyring.set_password(self.domain, 'authorization', self.authorization)

  # ----------------------------------------------------------------------------
  def _clear_credentials_impl(self) -> None:
    """Clear authorization from memory."""
    if self.authorization:
      self.authorization = '*' * len(self.authorization)
      self.authorization = ''

  # ----------------------------------------------------------------------------
  def _verify_exists_impl(self) -> bool:
    """Check if authorization is set.

    Returns:
      True if authorization is set, False otherwise
    """
    return bool(self.authorization)

  # ----------------------------------------------------------------------------
  def save(self) -> None:
    """Save authorization header to the system keyring.

    Stores the authorization header value under the configured domain.
    """
    logger.debug(f'Saving authorization to keyring domain: {self.domain}')
    keyring.set_password(self.domain, 'authorization', self.authorization)
    logger.info('Authorization saved successfully')

  # ----------------------------------------------------------------------------
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


# Backwards compatibility alias
Config = ZRConfig


# ==============================================================================
def main() -> None:
  """CLI entry point for config management."""
  c = Config()
  c.load()
  if c.verify_credentials_exist():
    print('Authorization is configured in keyring')
  else:
    print('No authorization found in keyring')


# ==============================================================================
if __name__ == '__main__':
  sys.exit(main())
