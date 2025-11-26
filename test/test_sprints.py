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
  from unittest.mock import patch

  from zpdatafetch.zp import ZP

  original_init = ZP.__init__

  def mock_init(self, skip_credential_check=False):
    original_init(self, skip_credential_check=True)
    self.init_client(
      httpx.Client(
        follow_redirects=True, transport=httpx.MockTransport(sprints_handler)
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
