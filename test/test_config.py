from keyrings.alt.file import PlaintextKeyring


def test_setup(config):
  assert config is not None


def test_setup_has_no_default_creds(config):
  assert config.username == ''
  assert config.password == ''


def test_domain_can_be_changed(config):
  config.domain = 'test-zpdatafetch'
  assert config.domain == 'test-zpdatafetch'


def test_load_config_has_no_creds_before_set(config):
  config.domain = 'test-zpdatafetch'
  config.load()
  assert config.username == ''
  assert config.password == ''


def test_after_load_config_has_creds(config):
  tuser = 'test_username'
  tpass = 'test_password'
  config.set_keyring(PlaintextKeyring())
  config.domain = 'test-zpdatafetch'
  config.setup(username=tuser, password=tpass)
  assert config.username == tuser
  assert config.password == tpass
