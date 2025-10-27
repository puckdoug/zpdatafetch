"""Tests for rate limiting integration in AsyncZR_obj and ZR_obj."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from zrdatafetch.async_zr import AsyncZR_obj
from zrdatafetch.rate_limiter import RateLimiter


# ===============================================================================
class TestAsyncZR_objRateLimiting:
  """Test AsyncZR_obj rate limiting integration."""

  @pytest.mark.anyio
  async def test_init_standard_tier(self):
    """Test AsyncZR_obj initializes with standard tier."""
    async with AsyncZR_obj() as zr:
      assert zr.rate_limiter.tier == 'standard'

  @pytest.mark.anyio
  async def test_init_premium_tier(self):
    """Test AsyncZR_obj initializes with premium tier."""
    async with AsyncZR_obj(premium=True) as zr:
      assert zr.rate_limiter.tier == 'premium'

  @pytest.mark.anyio
  async def test_rate_limiter_attribute(self):
    """Test AsyncZR_obj has rate_limiter attribute."""
    async with AsyncZR_obj() as zr:
      assert hasattr(zr, 'rate_limiter')
      assert isinstance(zr.rate_limiter, RateLimiter)

  @pytest.mark.anyio
  async def test_fetch_json_records_request_on_success(self):
    """Test successful requests are recorded for rate limiting."""
    async with AsyncZR_obj() as zr:
      # Mock the client to return a successful response
      mock_response = MagicMock()
      mock_response.status_code = 200
      mock_response.json = MagicMock(return_value={'name': 'Test'})
      mock_response.raise_for_status = MagicMock()  # Sync method, not async

      zr._client = AsyncMock()
      zr._client.request = AsyncMock(return_value=mock_response)

      # Check initial state
      status_before = zr.rate_limiter.get_status()
      assert status_before['endpoints']['riders_get']['used'] == 0

      # Make request
      result = await zr.fetch_json('/public/riders/123', method='GET')
      assert result == {'name': 'Test'}

      # Check request was recorded
      status_after = zr.rate_limiter.get_status()
      assert status_after['endpoints']['riders_get']['used'] == 1

  @pytest.mark.anyio
  async def test_fetch_json_detects_endpoint_type(self):
    """Test fetch_json correctly identifies endpoint types."""
    async with AsyncZR_obj() as zr:
      mock_response = MagicMock()
      mock_response.status_code = 200
      mock_response.json = MagicMock(return_value={})
      mock_response.raise_for_status = MagicMock()  # Sync method, not async

      zr._client = AsyncMock()
      zr._client.request = AsyncMock(return_value=mock_response)

      # Test clubs endpoint
      await zr.fetch_json('/public/clubs/123', method='GET')
      status = zr.rate_limiter.get_status()
      assert status['endpoints']['clubs']['used'] == 1
      assert status['endpoints']['riders_get']['used'] == 0

      # Test riders POST endpoint
      await zr.fetch_json('/public/riders', method='POST', json=[1, 2, 3])
      status = zr.rate_limiter.get_status()
      assert status['endpoints']['riders_post']['used'] == 1


# ===============================================================================
class TestRateLimiterErrorMessages:
  """Test rate limit error messages are helpful."""

  def test_rate_limit_status_reporting(self):
    """Test rate limiter status includes all required fields."""
    limiter = RateLimiter(tier='standard')
    status = limiter.get_status()

    assert status['tier'] == 'standard'
    assert 'endpoints' in status

    for endpoint in ['clubs', 'results', 'riders_get', 'riders_post']:
      assert endpoint in status['endpoints']
      ep_status = status['endpoints'][endpoint]
      assert 'used' in ep_status
      assert 'limit' in ep_status
      assert 'remaining' in ep_status
      assert 'window_seconds' in ep_status
      assert 'reset_in_seconds' in ep_status


# ===============================================================================
class TestPremiumTierEnablement:
  """Test premium tier provides higher limits."""

  def test_standard_tier_limits(self):
    """Test standard tier has lower limits."""
    limiter = RateLimiter(tier='standard')
    # Standard: riders_get = 5 per minute
    assert limiter.limits['riders_get'][0] == 5
    assert limiter.limits['riders_post'][0] == 1
    assert limiter.limits['clubs'][0] == 1

  def test_premium_tier_limits(self):
    """Test premium tier has higher limits."""
    limiter = RateLimiter(tier='premium')
    # Premium: riders_get = 10 per minute
    assert limiter.limits['riders_get'][0] == 10
    assert limiter.limits['riders_post'][0] == 10
    assert limiter.limits['clubs'][0] == 10

  def test_premium_vs_standard_riders_get(self):
    """Test riders GET endpoint shows clear premium advantage."""
    limiter_standard = RateLimiter(tier='standard')
    limiter_premium = RateLimiter(tier='premium')

    # Standard: 5 per min
    for i in range(5):
      limiter_standard.record_request('riders_get')
    assert not limiter_standard.can_request('riders_get')

    # Premium: 10 per min
    for i in range(10):
      limiter_premium.record_request('riders_get')
    assert not limiter_premium.can_request('riders_get')

    # Verify premium allows 2x more
    premium_limit = limiter_premium.limits['riders_get'][0]
    standard_limit = limiter_standard.limits['riders_get'][0]
    assert premium_limit == 2 * standard_limit

  def test_premium_vs_standard_batch_endpoint(self):
    """Test POST batch endpoint shows massive premium advantage."""
    limiter_standard = RateLimiter(tier='standard')
    limiter_premium = RateLimiter(tier='premium')

    # Standard: 1 per 15 min
    limiter_standard.record_request('riders_post')
    assert not limiter_standard.can_request('riders_post')

    # Premium: 10 per 15 min
    for i in range(10):
      limiter_premium.record_request('riders_post')
    assert not limiter_premium.can_request('riders_post')

    # Verify premium allows 10x more
    premium_limit = limiter_premium.limits['riders_post'][0]
    standard_limit = limiter_standard.limits['riders_post'][0]
    assert premium_limit == 10 * standard_limit

  def test_async_zr_obj_premium_mode(self):
    """Test AsyncZR_obj respects premium parameter."""
    import asyncio

    async def test():
      async with AsyncZR_obj(premium=False) as zr:
        assert zr.rate_limiter.tier == 'standard'

      async with AsyncZR_obj(premium=True) as zr:
        assert zr.rate_limiter.tier == 'premium'

    asyncio.run(test())


# ===============================================================================
class TestRateLimitingBasics:
  """Test basic rate limiting functionality without network."""

  def test_endpoint_type_detection(self):
    """Test endpoint type classification."""
    # Clubs
    assert RateLimiter.get_endpoint_type('GET', '/public/clubs/123') == 'clubs'
    assert RateLimiter.get_endpoint_type('GET', '/public/clubs/123/456') == 'clubs'

    # Results
    assert RateLimiter.get_endpoint_type('GET', '/public/results/789') == 'results'

    # Riders GET
    assert RateLimiter.get_endpoint_type('GET', '/public/riders/123') == 'riders_get'
    assert (
      RateLimiter.get_endpoint_type('GET', '/public/riders/123/1704067200')
      == 'riders_get'
    )

    # Riders POST
    assert RateLimiter.get_endpoint_type('POST', '/public/riders') == 'riders_post'
    assert (
      RateLimiter.get_endpoint_type('POST', '/public/riders/1704067200')
      == 'riders_post'
    )

    # Unknown
    assert RateLimiter.get_endpoint_type('GET', '/unknown') == 'unknown'

  def test_limit_enforcement(self):
    """Test that limits are enforced correctly."""
    limiter = RateLimiter(tier='standard')

    # Can make 5 requests to riders_get
    for i in range(5):
      assert limiter.can_request('riders_get') is True
      limiter.record_request('riders_get')

    # 6th request should be denied
    assert limiter.can_request('riders_get') is False

  def test_independent_endpoint_limits(self):
    """Test that limits are independent per endpoint."""
    limiter = RateLimiter(tier='standard')

    # Max out riders_get
    for i in range(5):
      limiter.record_request('riders_get')
    assert not limiter.can_request('riders_get')

    # clubs should still be available
    assert limiter.can_request('clubs') is True
    limiter.record_request('clubs')
    assert not limiter.can_request('clubs')

    # results should still be available
    assert limiter.can_request('results') is True
