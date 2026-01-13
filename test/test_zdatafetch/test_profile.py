"""Tests for Zwift profile data fetching."""

import json

import httpx
import pytest

from shared.exceptions import ConfigError, NetworkError
from zdatafetch.profile import ZwiftProfile


def test_profile_initialization():
  """Test ZwiftProfile initialization."""
  profile = ZwiftProfile()

  assert profile._raw == ""
  assert profile._fetched == {}
  assert profile.id == 0
  assert profile.firstName == ""
  assert profile.lastName == ""


def test_fetch_single_profile(combined_handler, mock_profile_data, monkeypatch):
  """Test fetching a single rider profile."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    # Fetch profile
    profile = ZwiftProfile()
    profile.fetch(550564)

    # Verify data was fetched and parsed
    assert profile.id == 550564
    assert profile.firstName == "Test"
    assert profile.lastName == "Rider"
    assert profile.ftp == 278

    # Verify internal data structures
    assert profile._fetched["id"] == 550564
    assert isinstance(profile._raw, str)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_multiple_profiles(combined_handler, monkeypatch):
  """Test fetching multiple rider profiles."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    # Fetch multiple profiles
    profiles = ZwiftProfile.fetch_multiple(550564, 123456, 789012)

    # Verify all profiles were fetched
    assert len(profiles) == 3
    assert 550564 in profiles
    assert 123456 in profiles
    assert 789012 in profiles

    # Verify each profile is a ZwiftProfile instance
    assert isinstance(profiles[550564], ZwiftProfile)
    assert profiles[550564].id == 550564

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_profile_not_found(combined_handler, monkeypatch):
  """Test fetching a non-existent profile."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()

    with pytest.raises(NetworkError, match="Rider 999999 not found"):
      profile.fetch(999999)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_without_credentials(monkeypatch):
  """Test fetching profile without credentials configured."""
  import zdatafetch.profile

  # Mock the config to return empty credentials
  class MockConfig:
    username = ""
    password = ""

    def load(self):
      pass

  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)

  profile = ZwiftProfile()

  with pytest.raises(ConfigError, match="Zwift credentials not found"):
    profile.fetch(550564)


def test_fetch_network_error(auth_handler, monkeypatch):
  """Test network error during profile fetch."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  def handler(request):
    if "auth/realms/zwift" in str(request.url):
      return auth_handler(request)
    if "/api/profiles/" in str(request.url):
      raise httpx.ConnectError("Connection failed")
    return httpx.Response(404)

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()

    with pytest.raises(NetworkError, match="Network error fetching profile"):
      profile.fetch(550564)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_timeout(auth_handler, monkeypatch):
  """Test timeout during profile fetch."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  def handler(request):
    if "auth/realms/zwift" in str(request.url):
      return auth_handler(request)
    if "/api/profiles/" in str(request.url):
      raise httpx.TimeoutException("Request timed out")
    return httpx.Response(404)

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()

    with pytest.raises(NetworkError, match="Request timed out"):
      profile.fetch(550564)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_attribute_access(combined_handler, monkeypatch):
  """Test attribute access to profile data."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()
    profile.fetch(550564)

    # Test explicit attributes
    assert profile.id == 550564
    assert profile.firstName == "Test"
    assert profile.lastName == "Rider"

    # Test fallback to _fetched for other fields
    assert profile.male is True
    assert profile.countryAlpha3 == "USA"

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_dictionary_access(combined_handler, monkeypatch):
  """Test dictionary-style access to profile data."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()
    profile.fetch(550564)

    # Test dictionary access
    assert profile["id"] == 550564
    assert profile["firstName"] == "Test"
    assert profile["ftp"] == 278

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_json_output(combined_handler, monkeypatch):
  """Test JSON serialization of profile data."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()
    profile.fetch(550564)

    json_output = profile.json()
    assert isinstance(json_output, str)

    # Verify it's valid JSON
    parsed = json.loads(json_output)
    assert parsed["id"] == 550564

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_raw_output(combined_handler, monkeypatch):
  """Test raw output access."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()
    profile.fetch(550564)

    raw_data = profile.raw()
    assert isinstance(raw_data, str)

    # Verify it's valid JSON string
    parsed = json.loads(raw_data)
    assert parsed["id"] == 550564

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_asdict_output(combined_handler, monkeypatch):
  """Test dictionary output access."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()
    profile.fetch(550564)

    dict_data = profile.asdict()
    assert isinstance(dict_data, dict)
    assert dict_data["id"] == 550564

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_str_representation(combined_handler, monkeypatch):
  """Test string representation of profile data."""
  import zdatafetch.auth
  import zdatafetch.config
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  # Mock the config to return credentials
  class MockConfig:
    username = "test@example.com"
    password = "testpassword"

    def load(self):
      pass

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client
  monkeypatch.setattr(zdatafetch.profile, "Config", MockConfig)


  try:
    profile = ZwiftProfile()
    profile.fetch(550564)

    str_output = str(profile)
    assert isinstance(str_output, str)
    assert "550564" in str_output
    assert "Test" in str_output
    assert "Rider" in str_output

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client
