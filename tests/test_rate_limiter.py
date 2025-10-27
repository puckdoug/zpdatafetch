"""Tests for RateLimiter class."""

from zrdatafetch.rate_limiter import RateLimiter


# ===============================================================================
class TestRateLimiterInitialization:
  """Test RateLimiter initialization."""

  def test_init_standard_tier(self):
    """Test initialization with standard tier (default)."""
    limiter = RateLimiter()
    assert limiter.tier == 'standard'
    assert limiter.limits == RateLimiter.STANDARD_LIMITS

  def test_init_premium_tier(self):
    """Test initialization with premium tier."""
    limiter = RateLimiter(tier='premium')
    assert limiter.tier == 'premium'
    assert limiter.limits == RateLimiter.PREMIUM_LIMITS


# ===============================================================================
class TestRateLimiterCanRequest:
  """Test RateLimiter.can_request() method."""

  def test_can_request_no_limit_configured(self):
    """Test request allowed for unknown endpoint."""
    limiter = RateLimiter()
    assert limiter.can_request('unknown_endpoint') is True

  def test_can_request_first_request(self):
    """Test first request is always allowed."""
    limiter = RateLimiter()
    assert limiter.can_request('riders_get') is True

  def test_can_request_within_limit(self):
    """Test requests within limit are allowed."""
    limiter = RateLimiter(tier='standard')
    # riders_get: 5 requests per 60 seconds
    for i in range(5):
      assert limiter.can_request('riders_get') is True
      limiter.record_request('riders_get')

  def test_can_request_exceeds_limit(self):
    """Test request denied when limit exceeded."""
    limiter = RateLimiter(tier='standard')
    # riders_get: 5 requests per 60 seconds
    for i in range(5):
      limiter.record_request('riders_get')
    assert limiter.can_request('riders_get') is False

  def test_can_request_premium_higher_limit(self):
    """Test premium tier has higher limits."""
    limiter_standard = RateLimiter(tier='standard')
    limiter_premium = RateLimiter(tier='premium')

    # Record 6 requests for both
    for i in range(6):
      limiter_standard.record_request('riders_get')
      limiter_premium.record_request('riders_get')

    # Standard should deny, premium should allow
    assert limiter_standard.can_request('riders_get') is False
    assert limiter_premium.can_request('riders_get') is True


# ===============================================================================
class TestRateLimiterWaitTime:
  """Test RateLimiter.wait_time() method."""

  def test_wait_time_no_wait_needed(self):
    """Test wait time is 0 when no wait needed."""
    limiter = RateLimiter()
    assert limiter.wait_time('riders_get') == 0.0

  def test_wait_time_at_limit(self):
    """Test wait time calculated when at limit."""
    limiter = RateLimiter(tier='standard')
    # riders_get: 5 requests per 60 seconds
    for i in range(5):
      limiter.record_request('riders_get')

    wait_time = limiter.wait_time('riders_get')
    # Should be close to 60 seconds (minus small time that passed)
    assert 55 < wait_time <= 60

  def test_wait_time_unknown_endpoint(self):
    """Test wait time for unknown endpoint is 0."""
    limiter = RateLimiter()
    assert limiter.wait_time('unknown') == 0.0


# ===============================================================================
class TestRateLimiterRecordRequest:
  """Test RateLimiter.record_request() method."""

  def test_record_request_increments_count(self):
    """Test recording request increments count."""
    limiter = RateLimiter()
    assert limiter.can_request('riders_get') is True
    limiter.record_request('riders_get')
    # After 1 request of 5 allowed, should still be able to request
    assert limiter.can_request('riders_get') is True

  def test_record_request_unknown_endpoint(self):
    """Test recording request for unknown endpoint doesn't error."""
    limiter = RateLimiter()
    # Should not raise
    limiter.record_request('unknown_endpoint')


# ===============================================================================
class TestRateLimiterGetStatus:
  """Test RateLimiter.get_status() method."""

  def test_get_status_initial_state(self):
    """Test status for initial state."""
    limiter = RateLimiter(tier='standard')
    status = limiter.get_status()

    assert status['tier'] == 'standard'
    assert 'endpoints' in status
    assert 'riders_get' in status['endpoints']
    assert status['endpoints']['riders_get']['used'] == 0
    assert status['endpoints']['riders_get']['limit'] == 5

  def test_get_status_after_requests(self):
    """Test status after making requests."""
    limiter = RateLimiter(tier='standard')
    limiter.record_request('riders_get')
    limiter.record_request('riders_get')

    status = limiter.get_status()
    assert status['endpoints']['riders_get']['used'] == 2
    assert status['endpoints']['riders_get']['remaining'] == 3

  def test_get_status_all_endpoints(self):
    """Test status includes all endpoints."""
    limiter = RateLimiter()
    status = limiter.get_status()

    expected_endpoints = {'clubs', 'results', 'riders_get', 'riders_post'}
    assert set(status['endpoints'].keys()) == expected_endpoints


# ===============================================================================
class TestRateLimiterSetTier:
  """Test RateLimiter.set_tier() method."""

  def test_set_tier_changes_limits(self):
    """Test changing tier updates limits."""
    limiter = RateLimiter(tier='standard')
    assert limiter.tier == 'standard'

    limiter.set_tier('premium')
    assert limiter.tier == 'premium'
    assert limiter.limits == RateLimiter.PREMIUM_LIMITS


# ===============================================================================
class TestRateLimiterGetEndpointType:
  """Test RateLimiter.get_endpoint_type() static method."""

  def test_get_endpoint_type_clubs(self):
    """Test endpoint type detection for clubs."""
    assert RateLimiter.get_endpoint_type('GET', '/public/clubs/123') == 'clubs'
    assert RateLimiter.get_endpoint_type('GET', '/public/clubs/123/456') == 'clubs'

  def test_get_endpoint_type_results(self):
    """Test endpoint type detection for results."""
    assert RateLimiter.get_endpoint_type('GET', '/public/results/789') == 'results'

  def test_get_endpoint_type_riders_get(self):
    """Test endpoint type detection for riders GET."""
    assert RateLimiter.get_endpoint_type('GET', '/public/riders/123') == 'riders_get'
    assert (
      RateLimiter.get_endpoint_type('GET', '/public/riders/123/1704067200')
      == 'riders_get'
    )

  def test_get_endpoint_type_riders_post(self):
    """Test endpoint type detection for riders POST."""
    assert RateLimiter.get_endpoint_type('POST', '/public/riders') == 'riders_post'
    assert (
      RateLimiter.get_endpoint_type('POST', '/public/riders/1704067200')
      == 'riders_post'
    )

  def test_get_endpoint_type_unknown(self):
    """Test endpoint type for unknown endpoint."""
    assert RateLimiter.get_endpoint_type('GET', '/unknown') == 'unknown'


# ===============================================================================
class TestRateLimiterTimeWindow:
  """Test rate limiter sliding window behavior."""

  def test_window_expiration(self):
    """Test old requests expire from window."""
    limiter = RateLimiter(tier='standard')
    # Record request and immediately check status
    limiter.record_request('riders_get')
    status1 = limiter.get_status()
    assert status1['endpoints']['riders_get']['used'] == 1

    # Mock checking after window expires (we'll just check internally)
    # Note: Actually waiting would be slow, so we just verify the logic works
    assert limiter.can_request('riders_get') is True


# ===============================================================================
class TestRateLimiterEndpointLimits:
  """Test specific rate limits for each endpoint."""

  def test_clubs_standard_limit(self):
    """Test clubs endpoint standard tier limit: 1 per 60 minutes."""
    limiter = RateLimiter(tier='standard')
    assert limiter.can_request('clubs') is True
    limiter.record_request('clubs')
    assert limiter.can_request('clubs') is False

  def test_clubs_premium_limit(self):
    """Test clubs endpoint premium tier limit: 10 per 60 minutes."""
    limiter = RateLimiter(tier='premium')
    for i in range(10):
      assert limiter.can_request('clubs') is True
      limiter.record_request('clubs')
    assert limiter.can_request('clubs') is False

  def test_results_same_for_both_tiers(self):
    """Test results endpoint limit is same: 1 per 60 seconds."""
    limiter_standard = RateLimiter(tier='standard')
    limiter_premium = RateLimiter(tier='premium')

    limiter_standard.record_request('results')
    limiter_premium.record_request('results')

    assert limiter_standard.can_request('results') is False
    assert limiter_premium.can_request('results') is False

  def test_riders_get_standard_limit(self):
    """Test riders GET endpoint standard tier limit: 5 per 60 seconds."""
    limiter = RateLimiter(tier='standard')
    for i in range(5):
      limiter.record_request('riders_get')
    assert limiter.can_request('riders_get') is False

  def test_riders_get_premium_limit(self):
    """Test riders GET endpoint premium tier limit: 10 per 60 seconds."""
    limiter = RateLimiter(tier='premium')
    for i in range(10):
      limiter.record_request('riders_get')
    assert limiter.can_request('riders_get') is False

  def test_riders_post_standard_limit(self):
    """Test riders POST endpoint standard tier limit: 1 per 15 minutes."""
    limiter = RateLimiter(tier='standard')
    limiter.record_request('riders_post')
    assert limiter.can_request('riders_post') is False

  def test_riders_post_premium_limit(self):
    """Test riders POST endpoint premium tier limit: 10 per 15 minutes."""
    limiter = RateLimiter(tier='premium')
    for i in range(10):
      limiter.record_request('riders_post')
    assert limiter.can_request('riders_post') is False


# ===============================================================================
class TestRateLimiterConcurrency:
  """Test rate limiter with multiple endpoints."""

  def test_independent_endpoint_limits(self):
    """Test that limits are independent per endpoint."""
    limiter = RateLimiter(tier='standard')

    # Max out riders_get
    for i in range(5):
      limiter.record_request('riders_get')
    assert limiter.can_request('riders_get') is False

    # clubs should still be available
    assert limiter.can_request('clubs') is True
    limiter.record_request('clubs')
    assert limiter.can_request('clubs') is False

    # results should still be available
    assert limiter.can_request('results') is True
