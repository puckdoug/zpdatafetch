"""Tests for Zwift profile data fetching."""

import json

import httpx
import pytest

from shared.exceptions import NetworkError
from zdatafetch.profile import ZwiftProfile


def test_profile_initialization(mock_auth):
  """Test ZwiftProfile initialization."""
  profile = ZwiftProfile(mock_auth)

  assert profile.auth == mock_auth
  assert profile._raw == {}
  assert profile._fetched == {}


def test_fetch_single_profile(
  mock_auth,
  combined_handler,
  mock_profile_data,
  mock_token_response,
):
  """Test fetching a single rider profile."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    # Login first
    mock_auth.login()

    # Fetch profile
    profile = ZwiftProfile(mock_auth)
    profile.fetch(550564)

    # Verify data was fetched
    assert 550564 in profile._fetched
    assert profile._fetched[550564]['id'] == 550564
    assert profile._fetched[550564]['firstName'] == 'Test'
    assert profile._fetched[550564]['lastName'] == 'Rider'

    # Verify raw data was stored
    assert 550564 in profile._raw
    assert isinstance(profile._raw[550564], str)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_multiple_profiles(mock_auth, combined_handler):
  """Test fetching multiple rider profiles."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)
    profile.fetch(550564, 123456, 789012)

    # Verify all profiles were fetched
    assert len(profile._fetched) == 3
    assert 550564 in profile._fetched
    assert 123456 in profile._fetched
    assert 789012 in profile._fetched

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_profile_not_found(mock_auth, combined_handler):
  """Test fetching a non-existent profile."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)

    with pytest.raises(NetworkError, match='Rider 999999 not found'):
      profile.fetch(999999)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_without_authentication(mock_auth):
  """Test fetching profile without authentication."""

  def handler(request):
    if '/api/profiles/' in str(request.url):
      return httpx.Response(401, text='Unauthorized')
    return httpx.Response(404)

  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(handler))

  zdatafetch.profile.httpx.Client = mock_client

  try:
    # Don't login - should fail
    mock_auth.access_token = None

    profile = ZwiftProfile(mock_auth)

    with pytest.raises(RuntimeError, match='No valid token available'):
      profile.fetch(550564)

  finally:
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_network_error(mock_auth, auth_handler):
  """Test network error during profile fetch."""

  def handler(request):
    if 'auth/realms/zwift' in str(request.url):
      return auth_handler(request)
    if '/api/profiles/' in str(request.url):
      raise httpx.ConnectError('Connection failed')
    return httpx.Response(404)

  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)

    with pytest.raises(NetworkError, match='Network error fetching profile'):
      profile.fetch(550564)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_fetch_timeout(mock_auth, auth_handler):
  """Test timeout during profile fetch."""

  def handler(request):
    if 'auth/realms/zwift' in str(request.url):
      return auth_handler(request)
    if '/api/profiles/' in str(request.url):
      raise httpx.TimeoutException('Request timed out')
    return httpx.Response(404)

  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)

    with pytest.raises(NetworkError, match='Request timed out'):
      profile.fetch(550564)

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_json_output(mock_auth, combined_handler):
  """Test JSON serialization of profile data."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)
    profile.fetch(550564)

    json_output = profile.json()
    assert isinstance(json_output, str)

    # Verify it's valid JSON
    parsed = json.loads(json_output)
    # JSON stores integer keys as strings
    assert '550564' in parsed or 550564 in parsed
    rider_data = parsed.get('550564') or parsed.get(550564)
    assert rider_data['id'] == 550564

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_raw_output(mock_auth, combined_handler):
  """Test raw output access."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)
    profile.fetch(550564)

    raw_data = profile.raw()
    assert isinstance(raw_data, dict)
    assert 550564 in raw_data
    assert isinstance(raw_data[550564], str)

    # Verify it's valid JSON string
    parsed = json.loads(raw_data[550564])
    assert parsed['id'] == 550564

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_asdict_output(mock_auth, combined_handler):
  """Test dictionary output access."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)
    profile.fetch(550564)

    dict_data = profile.asdict()
    assert isinstance(dict_data, dict)
    assert 550564 in dict_data
    assert dict_data[550564]['id'] == 550564

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_get_specific_rider(mock_auth, combined_handler):
  """Test getting data for a specific rider."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)
    profile.fetch(550564, 123456)

    # Get specific rider
    rider_data = profile.get(550564)
    assert rider_data is not None
    assert rider_data['id'] == 550564

    # Get non-existent rider
    missing_data = profile.get(999999)
    assert missing_data is None

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client


def test_str_representation(mock_auth, combined_handler):
  """Test string representation of profile data."""
  import zdatafetch.auth
  import zdatafetch.profile

  original_client = httpx.Client

  def mock_client(*args, **kwargs):
    return original_client(transport=httpx.MockTransport(combined_handler))

  zdatafetch.auth.httpx.Client = mock_client
  zdatafetch.profile.httpx.Client = mock_client

  try:
    mock_auth.login()

    profile = ZwiftProfile(mock_auth)
    profile.fetch(550564)

    str_output = str(profile)
    assert isinstance(str_output, str)
    assert '550564' in str_output

  finally:
    zdatafetch.auth.httpx.Client = original_client
    zdatafetch.profile.httpx.Client = original_client
