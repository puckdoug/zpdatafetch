from unittest.mock import patch

import httpx

from zpdatafetch.zpracesprint import ZPRaceSprint, ZPRiderSprint


def test_zpracesprint_empty_instantiation():
  """Test that ZPRaceSprint can be instantiated with no arguments."""
  obj = ZPRaceSprint()
  assert obj is not None
  assert len(obj) == 0
  assert obj.aslist() == []


def test_zpridersprint_empty_instantiation():
  """Test that ZPRiderSprint can be instantiated with no arguments."""
  obj = ZPRiderSprint()
  assert obj is not None
  assert obj.zwift_id == 0
  assert obj.name == ''
  assert obj.category == ''


def test_sprints(sprints):
  assert sprints is not None


def test_sprints_initialization(sprints):
  assert sprints._raw == {}


def test_sprints_fetch_race_sprints(
  sprints,
  sprints_test_data,
  primes_test_data,
  sprints_handler,
):
  from zpdatafetch.async_zp import AsyncZP
  from zpdatafetch.zpracesprint import ZPRaceSprint

  original_init = AsyncZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self._client = httpx.AsyncClient(
      follow_redirects=True,
      transport=httpx.MockTransport(sprints_handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    # Mock primes.afetch to avoid real API call
    with patch.object(sprints.primes, 'afetch') as mock_primes_afetch:
      mock_primes_afetch.return_value = primes_test_data
      sprints.primes.raw = primes_test_data

      race_sprints = sprints.fetch(3590800)
      assert 3590800 in race_sprints
      assert isinstance(race_sprints[3590800], ZPRaceSprint)
      # Verify asdict() returns typed fields (not API format)
      asdict_result = race_sprints[3590800].asdict()
      assert 'race_id' in asdict_result
      assert 'data' in asdict_result
      mock_primes_afetch.assert_called_once_with(3590800)
  finally:
    AsyncZP.__init__ = original_init


def test_sprints_shares_zp_session_with_primes(
  sprints,
  sprints_test_data,
  primes_test_data,
  sprints_handler,
):
  """Test that sprints shares the AsyncZP session with primes to avoid double login."""
  from unittest.mock import patch

  from zpdatafetch.async_zp import AsyncZP

  original_init = AsyncZP.__init__
  login_count = {'count': 0}

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    login_count['count'] += 1  # Track how many AsyncZP instances are created
    self._client = httpx.AsyncClient(
      follow_redirects=True,
      transport=httpx.MockTransport(sprints_handler),
    )

  AsyncZP.__init__ = mock_init

  try:
    # Mock primes.afetch to avoid real API call but verify set_session is called
    with patch.object(sprints.primes, 'afetch') as mock_primes_afetch:
      with patch.object(sprints.primes, 'set_session') as mock_set_session:
        mock_primes_afetch.return_value = primes_test_data
        sprints.primes.raw = primes_test_data

        sprints.fetch(3590800)

        # Verify only ONE AsyncZP instance was created (not two)
        assert login_count['count'] == 1, (
          'Should only create one AsyncZP session'
        )

        # Verify set_session was called to share the session
        assert mock_set_session.called, (
          'Should call set_session to share AsyncZP instance'
        )
        # Verify the session passed is an AsyncZP instance
        call_args = mock_set_session.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], AsyncZP), (
          'Should pass AsyncZP instance to primes'
        )

        # Verify primes.afetch was called
        mock_primes_afetch.assert_called_once_with(3590800)
  finally:
    AsyncZP.__init__ = original_init
