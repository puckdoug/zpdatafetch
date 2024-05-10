import sys
import keyring
from getpass import getpass
# ===============================================================================


class Config:
  verbose: bool = False

  # -----------------------------------------------------------------------------
  def __init__(self):
    self.load()

  # -----------------------------------------------------------------------------
  def save(self):
    keyring.set_password('zp_data', 'username', self.username)
    keyring.set_password('zp_data', 'password', self.password)

  # -----------------------------------------------------------------------------
  def load(self):
    self.username = keyring.get_password('zp_data', 'username')
    self.password = keyring.get_password('zp_data', 'password')

  # -----------------------------------------------------------------------------
  def setup(self, username='', password=''):
    if username:
      self.username = username
    else:
      self.username = input('zwiftpower username (for use with zp_data): ')
      keyring.set_password('zp_data', 'username', self.username)

    if password:
      self.password = password
    else:
      self.password = getpass('zwiftpower password (for use with zp_data): ')
      keyring.set_password('zp_data', 'password', self.password)

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
