"""Tests for zrdatafetch Config class.

Tests the configuration management for Zwiftracing API credentials
stored in system keyring.
"""

from keyrings.alt.file import PlaintextKeyring

from zrdatafetch import Config


# ===============================================================================
class TestConfigSetup:
  """Test Config initialization and setup."""

  def test_setup(self):
    """Test that Config can be instantiated."""
    config = Config()
    assert config is not None

  def test_setup_has_no_default_auth(self):
    """Test that Config starts with empty authorization."""
    config = Config()
    assert config.authorization == ''

  def test_domain_default(self):
    """Test that default domain is 'zrdatafetch'."""
    config = Config()
    assert config.domain == 'zrdatafetch'

  def test_domain_can_be_changed(self):
    """Test that domain can be changed."""
    config = Config()
    config.domain = 'test-zrdatafetch'
    assert config.domain == 'test-zrdatafetch'


# ===============================================================================
class TestConfigKeyring:
  """Test keyring operations."""

  def test_set_keyring(self):
    """Test setting a custom keyring backend."""
    config = Config()
    kr = PlaintextKeyring()
    config.set_keyring(kr)
    # Should not raise any exception

  def test_load_config_has_no_auth_before_set(self):
    """Test that load returns empty auth before credentials are set."""
    config = Config()
    config.set_keyring(PlaintextKeyring())
    config.domain = 'test-zrdatafetch-load'
    config.load()
    assert config.authorization == ''

  def test_after_setup_config_has_auth(self):
    """Test that setup stores and can be loaded."""
    config = Config()
    config.set_keyring(PlaintextKeyring())
    config.domain = 'test-zrdatafetch-setup'
    test_auth = 'test-authorization-123abc'

    config.setup(authorization=test_auth)
    assert config.authorization == test_auth

  def test_load_retrieves_saved_auth(self):
    """Test that load retrieves previously saved authorization."""
    # Set up initial config
    config1 = Config()
    config1.set_keyring(PlaintextKeyring())
    config1.domain = 'test-zrdatafetch-retrieve'
    test_auth = 'test-auth-retrieve-value'
    config1.setup(authorization=test_auth)

    # Load in new config instance
    config2 = Config()
    config2.set_keyring(PlaintextKeyring())
    config2.domain = 'test-zrdatafetch-retrieve'
    config2.load()

    assert config2.authorization == test_auth


# ===============================================================================
class TestConfigCredentialManagement:
  """Test credential management methods."""

  def test_verify_credentials_exist_when_empty(self):
    """Test verify_credentials_exist returns False when empty."""
    config = Config()
    assert config.verify_credentials_exist() is False

  def test_verify_credentials_exist_when_set(self):
    """Test verify_credentials_exist returns True when auth is set."""
    config = Config()
    config.authorization = 'some-auth-value'
    assert config.verify_credentials_exist() is True

  def test_clear_credentials(self):
    """Test that clear_credentials clears authorization."""
    config = Config()
    config.authorization = 'sensitive-data'
    config.clear_credentials()
    assert config.authorization == ''

  def test_clear_credentials_overwrites_first(self):
    """Test that clear overwrites before clearing."""
    config = Config()
    original_auth = 'secret-value-12345'
    config.authorization = original_auth
    config.clear_credentials()
    # Should be cleared (empty string)
    assert config.authorization == ''


# ===============================================================================
class TestConfigSaveLoad:
  """Test save and load operations."""

  def test_save_and_load_cycle(self):
    """Test complete save/load cycle."""
    test_domain = 'test-zrdatafetch-cycle'
    test_auth = 'auth-value-for-cycle'

    # Create and save
    config1 = Config()
    config1.set_keyring(PlaintextKeyring())
    config1.domain = test_domain
    config1.authorization = test_auth
    config1.save()

    # Load in new instance
    config2 = Config()
    config2.set_keyring(PlaintextKeyring())
    config2.domain = test_domain
    config2.load()

    assert config2.authorization == test_auth

  def test_save_without_auth(self):
    """Test that save works with empty authorization."""
    config = Config()
    config.set_keyring(PlaintextKeyring())
    config.domain = 'test-zrdatafetch-empty-save'
    config.authorization = ''
    # Should not raise exception
    config.save()


# ===============================================================================
class TestConfigDomainOverride:
  """Test test domain override functionality."""

  def test_test_domain_override_applied(self):
    """Test that _test_domain_override is used when set."""
    Config._test_domain_override = 'test-override-domain'
    config = Config()
    assert config.domain == 'test-override-domain'
    # Clean up
    Config._test_domain_override = None

  def test_default_domain_when_no_override(self):
    """Test that default domain is used when no override."""
    Config._test_domain_override = None
    config = Config()
    assert config.domain == 'zrdatafetch'
