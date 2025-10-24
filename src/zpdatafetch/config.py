import sys
from getpass import getpass
from typing import Any, Optional

import keyring

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

  verbose: bool = False
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
    # Use test domain if set
    if Config._test_domain_override:
      self.domain = Config._test_domain_override

  #   self.load()

  # -----------------------------------------------------------------------------
  def set_keyring(self, kr: Any) -> None:
    """Set a custom keyring backend.

    Args:
      kr: Keyring backend instance (e.g., PlaintextKeyring for testing)
    """
    keyring.set_keyring(kr)

  # -----------------------------------------------------------------------------
  def replace_domain(self, domain: str) -> None:
    """Change the keyring service domain.

    Args:
      domain: New domain name to use for keyring operations
    """
    self.domain = domain

  # -----------------------------------------------------------------------------
  def save(self) -> None:
    """Save current credentials to the system keyring.

    Stores both username and password under the configured domain.
    """
    keyring.set_password(self.domain, 'username', self.username)
    keyring.set_password(self.domain, 'password', self.password)

  # -----------------------------------------------------------------------------
  def load(self) -> None:
    """Load credentials from the system keyring.

    Retrieves username and password from the configured domain.
    Updates instance attributes if credentials are found.
    """
    u = keyring.get_password(self.domain, 'username')
    if u:
      self.username = u
    p = keyring.get_password(self.domain, 'password')
    if p:
      self.password = p

  # -----------------------------------------------------------------------------
  def setup(self, username: str = '', password: str = '') -> None:
    """Configure Zwiftpower credentials interactively or programmatically.

    If username/password are not provided, prompts the user interactively.
    Saves credentials to keyring after collection.

    Args:
      username: Zwiftpower username (prompts if empty)
      password: Zwiftpower password (prompts securely if empty)
    """
    if username:
      self.username = username
    else:
      self.username = input('zwiftpower username (for use with zpdatafetch): ')
      keyring.set_password(self.domain, 'username', self.username)

    if password:
      self.password = password
    else:
      self.password = getpass(
        'zwiftpower password (for use with zpdatafetch): ',
      )
      keyring.set_password(self.domain, 'password', self.password)

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
