import sys
from getpass import getpass
from typing import Any, Optional

import keyring

# ===============================================================================


class Config:
  verbose: bool = False
  domain: str = 'zpdatafetch'
  username: str = ''
  password: str = ''
  _test_domain_override: str | None = None  # Class variable for test domain override

  # -----------------------------------------------------------------------------
  def __init__(self) -> None:
    self.kr: Any = keyring.get_keyring()
    # Use test domain if set
    if Config._test_domain_override:
      self.domain = Config._test_domain_override

  #   self.load()

  # -----------------------------------------------------------------------------
  def set_keyring(self, kr: Any) -> None:
    keyring.set_keyring(kr)

  # -----------------------------------------------------------------------------
  def replace_domain(self, domain: str) -> None:
    self.domain = domain

  # -----------------------------------------------------------------------------
  def save(self) -> None:
    keyring.set_password(self.domain, 'username', self.username)
    keyring.set_password(self.domain, 'password', self.password)

  # -----------------------------------------------------------------------------
  def load(self) -> None:
    u = keyring.get_password(self.domain, 'username')
    if u:
      self.username = u
    p = keyring.get_password(self.domain, 'password')
    if p:
      self.password = p

  # -----------------------------------------------------------------------------
  def setup(self, username: str = '', password: str = '') -> None:
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
    print(f'username: {self.username}')
    print(f'password: {self.password}')


# ===============================================================================
def main() -> None:
  c = Config()
  c.dump()


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
