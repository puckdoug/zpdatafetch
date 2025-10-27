"""Tests for zrdatafetch base class (ZR_obj).

Tests the common functionality provided by the ZR_obj base class including
HTTP client management, error handling, and JSON serialization.
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from zrdatafetch.exceptions import ZRNetworkError
from zrdatafetch.zr import ZR_obj


# ===============================================================================
class TestZR_objClientManagement:
  """Test HTTP client management and pooling."""

  def test_get_client_creates_client(self):
    """Test that get_client creates an httpx.Client instance."""
    # Clean up any existing client
    ZR_obj._client = None

    # Mock httpx.Client to prevent real connections
    with patch('httpx.Client') as mock_client_class:
      mock_client = MagicMock()
      mock_client.base_url = 'https://zwift-ranking.herokuapp.com'
      mock_client_class.return_value = mock_client

      client = ZR_obj.get_client()

      assert client is mock_client
      mock_client_class.assert_called_once()

  def test_get_client_reuses_existing_client(self):
    """Test that get_client reuses the existing client."""
    # Clean up and create a fresh client
    ZR_obj._client = None

    with patch('httpx.Client') as mock_client_class:
      mock_client = MagicMock()
      mock_client_class.return_value = mock_client

      client1 = ZR_obj.get_client()
      client2 = ZR_obj.get_client()

      assert client1 is client2
      # Should only create client once
      mock_client_class.assert_called_once()

  def test_close_client_closes_connection(self):
    """Test that close_client properly closes the connection."""
    ZR_obj._client = None

    with patch('httpx.Client') as mock_client_class:
      mock_client = MagicMock()
      mock_client_class.return_value = mock_client

      ZR_obj.get_client()
      ZR_obj.close_client()

      assert ZR_obj._client is None
      mock_client.close.assert_called_once()

  def test_close_client_when_none(self):
    """Test that close_client handles None gracefully."""
    ZR_obj._client = None
    # Should not raise any exception
    ZR_obj.close_client()
    assert ZR_obj._client is None


# ===============================================================================
class TestZR_objFetchJson:
  """Test JSON fetching functionality."""

  def test_fetch_json_success(self):
    """Test successful JSON fetch from endpoint."""
    obj = ZR_obj()

    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {'id': 123, 'name': 'Test Rider'}

    with patch.object(ZR_obj, 'get_client') as mock_get_client:
      mock_client = MagicMock()
      mock_client.get.return_value = mock_response
      mock_get_client.return_value = mock_client

      result = obj.fetch_json('/public/riders/123')

      assert result == {'id': 123, 'name': 'Test Rider'}
      mock_client.get.assert_called_once()

  def test_fetch_json_http_error(self):
    """Test that HTTP errors are properly wrapped."""
    obj = ZR_obj()

    # Create a mock HTTP error
    response = MagicMock()
    response.status_code = 404
    response.reason_phrase = 'Not Found'
    http_error = httpx.HTTPStatusError('404 Not Found', request=None, response=response)

    with patch.object(ZR_obj, 'get_client') as mock_get_client:
      mock_client = MagicMock()
      mock_client.get.side_effect = http_error
      mock_get_client.return_value = mock_client

      with pytest.raises(ZRNetworkError):
        obj.fetch_json('/public/riders/999')

  def test_fetch_json_network_error(self):
    """Test that network errors are properly wrapped."""
    obj = ZR_obj()

    # Create a mock network error
    network_error = httpx.RequestError('Connection failed')

    with patch.object(ZR_obj, 'get_client') as mock_get_client:
      mock_client = MagicMock()
      mock_client.get.side_effect = network_error
      mock_get_client.return_value = mock_client

      with pytest.raises(ZRNetworkError):
        obj.fetch_json('/public/riders/123')

  def test_fetch_json_invalid_json(self):
    """Test that invalid JSON responses are properly wrapped."""
    obj = ZR_obj()

    # Create a mock response that raises JSONDecodeError
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError(
      'Invalid JSON',
      '',
      0,
    )

    with patch.object(ZR_obj, 'get_client') as mock_get_client:
      mock_client = MagicMock()
      mock_client.get.return_value = mock_response
      mock_get_client.return_value = mock_client

      with pytest.raises(ZRNetworkError):
        obj.fetch_json('/public/riders/123')


# ===============================================================================
class TestZR_objSerialization:
  """Test JSON and dict serialization."""

  def test_json_method_calls_to_dict(self):
    """Test that json() method uses to_dict()."""

    # Create a minimal subclass that implements to_dict
    class TestZRObject(ZR_obj):
      def to_dict(self):
        return {'id': 123, 'name': 'Test'}

    obj = TestZRObject()
    json_str = obj.json()

    # Verify it's valid JSON
    parsed = json.loads(json_str)
    assert parsed == {'id': 123, 'name': 'Test'}

  def test_to_dict_not_implemented(self):
    """Test that to_dict raises NotImplementedError in base class."""
    obj = ZR_obj()

    with pytest.raises(NotImplementedError):
      obj.to_dict()

  def test_json_not_implemented(self):
    """Test that json raises NotImplementedError when to_dict not overridden."""
    obj = ZR_obj()

    with pytest.raises(NotImplementedError):
      obj.json()


# ===============================================================================
class TestZR_objIntegration:
  """Integration tests for ZR_obj."""

  def test_multiple_instances_share_client(self):
    """Test that multiple instances share the same HTTP client."""
    ZR_obj._client = None

    with patch('httpx.Client') as mock_client_class:
      mock_client = MagicMock()
      mock_client_class.return_value = mock_client

      obj1 = ZR_obj()
      obj2 = ZR_obj()

      client1 = obj1.get_client()
      client2 = obj2.get_client()

      assert client1 is client2
      # Should only create client once even with multiple instances
      mock_client_class.assert_called_once()

  def test_client_lifecycle(self):
    """Test complete client lifecycle."""
    ZR_obj._client = None

    with patch('httpx.Client') as mock_client_class:
      mock_client1 = MagicMock()
      mock_client3 = MagicMock()
      mock_client_class.side_effect = [mock_client1, mock_client3]

      # Create client
      obj = ZR_obj()
      client1 = obj.get_client()
      assert ZR_obj._client is not None
      assert client1 is mock_client1

      # Reuse client
      client2 = obj.get_client()
      assert client1 is client2

      # Close client
      obj.close_client()
      assert ZR_obj._client is None
      mock_client1.close.assert_called_once()

      # Create new client
      client3 = obj.get_client()
      assert client3 is not client1
      assert client3 is mock_client3
