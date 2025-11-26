from unittest.mock import patch

import httpx


def test_sprints(sprints):
  assert sprints is not None


def test_sprints_initialization(sprints):
  assert sprints.raw == {}


def test_sprints_fetch_race_sprints(
  sprints,
  sprints_test_data,
  primes_test_data,
  sprints_handler,
):
  from zpdatafetch.zp import ZP

  original_init = ZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self.init_client(
      httpx.Client(
        follow_redirects=True,
        transport=httpx.MockTransport(sprints_handler),
      ),
    )

  ZP.__init__ = mock_init

  try:
    # Mock primes.fetch to avoid real API call
    with patch.object(sprints.primes, 'fetch') as mock_primes_fetch:
      mock_primes_fetch.return_value = primes_test_data
      sprints.primes.raw = primes_test_data

      race_sprints = sprints.fetch(3590800)
      assert 3590800 in race_sprints
      assert race_sprints[3590800] == sprints_test_data
      mock_primes_fetch.assert_called_once_with(3590800)
  finally:
    ZP.__init__ = original_init


def test_sprints_shares_zp_session_with_primes(
  sprints,
  sprints_test_data,
  primes_test_data,
  sprints_handler,
):
  """Test that sprints shares the ZP session with primes to avoid double login."""
  from unittest.mock import patch

  from zpdatafetch.zp import ZP

  original_init = ZP.__init__
  login_count = {'count': 0}

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    login_count['count'] += 1  # Track how many ZP instances are created
    self.init_client(
      httpx.Client(
        follow_redirects=True,
        transport=httpx.MockTransport(sprints_handler),
      ),
    )

  ZP.__init__ = mock_init

  try:
    # Mock primes.fetch to avoid real API call but verify set_zp_session is called
    with patch.object(sprints.primes, 'fetch') as mock_primes_fetch:
      with patch.object(sprints.primes, 'set_zp_session') as mock_set_zp_session:
        mock_primes_fetch.return_value = primes_test_data
        sprints.primes.raw = primes_test_data

        sprints.fetch(3590800)

        # Verify only ONE ZP instance was created (not two)
        assert login_count['count'] == 1, 'Should only create one ZP session'

        # Verify set_zp_session was called to share the session
        assert (
          mock_set_zp_session.called
        ), 'Should call set_zp_session to share ZP instance'
        # Verify the session passed is a ZP instance
        call_args = mock_set_zp_session.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], ZP), 'Should pass ZP instance to primes'

        # Verify primes.fetch was called
        mock_primes_fetch.assert_called_once_with(3590800)
  finally:
    ZP.__init__ = original_init
