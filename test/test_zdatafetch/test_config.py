"""Tests for Zwift API configuration."""


from zdatafetch.config import Config


def test_config_service_name():
  """Test that Config uses correct service name."""
  assert Config._service_name == 'zdatafetch'
  assert Config._username_key == 'username'
  assert Config._password_key == 'password'


def test_config_inherits_from_base():
  """Test that Config inherits from BaseConfig."""
  from shared.config import BaseConfig

  assert issubclass(Config, BaseConfig)


def test_config_class_attributes():
  """Test that Config has required class attributes."""
  assert hasattr(Config, '_service_name')
  assert hasattr(Config, '_username_key')
  assert hasattr(Config, '_password_key')
