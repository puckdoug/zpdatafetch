import sys
import keyring
from getpass import getpass
# ===============================================================================


class Config:
  verbose: bool = False
  domain: str = 'zp_data'
  username: str = None
  password: str = None
  keyring: keyring.backend.KeyringBackend

  # -----------------------------------------------------------------------------
  def __init__(self):
    self.keyring = keyring.get_keyring()

  #   self.load()

  # -----------------------------------------------------------------------------
  def set_keyring(self, kr):
    keyring.set_keyring(kr)

  # -----------------------------------------------------------------------------
  def replace_domain(self, domain):
    self.domain = domain

  # -----------------------------------------------------------------------------
  def save(self):
    keyring.set_password(self.domain, 'username', self.username)
    keyring.set_password(self.domain, 'password', self.password)

  # -----------------------------------------------------------------------------
  def load(self):
    self.username = keyring.get_password(self.domain, 'username')
    self.password = keyring.get_password(self.domain, 'password')

  # -----------------------------------------------------------------------------
  def setup(self, username='', password=''):
    if username:
      self.username = username
    else:
      self.username = input('zwiftpower username (for use with zp_data): ')
      keyring.set_password(self.domain, 'username', self.username)

    if password:
      self.password = password
    else:
      self.password = getpass('zwiftpower password (for use with zp_data): ')
      keyring.set_password(self.domain, 'password', self.password)

  # -----------------------------------------------------------------------------
  def dump(self):
    print(f'username: {self.username}')
    print(f'password: {self.password}')


# ===============================================================================
def main():
  c = Config()
  c.dump()


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
