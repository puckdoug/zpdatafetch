"""Tests for Sprints with async (afetch) methods."""

from unittest.mock import AsyncMock, patch

import httpx2
import pytest

from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.zpracesprint import ZPRaceSprint
from zpdatafetch.zpsprintsfetch import ZPSprintsFetch


@pytest.mark.anyio
async def test_async_sprints_fetch(
  sprints_test_data,
  primes_test_data,
  sprints_handler,
):
  """Test AsyncSprints fetch functionality."""
  async with AsyncZP(skip_credential_check=True) as zp:
    zp.username = 'testuser'
    zp.password = 'testpass'
    await zp.init_client(
      httpx2.AsyncClient(
        follow_redirects=True,
        transport=httpx2.MockTransport(sprints_handler),
      ),
    )

    sprints = ZPSprintsFetch()
    sprints.set_session(zp)

    # Mock primes.afetch to avoid real API call
    with patch.object(
      sprints.primes,
      'afetch',
      new_callable=AsyncMock,
    ) as mock_primes_afetch:
      mock_primes_afetch.return_value = primes_test_data
      sprints.primes.raw = primes_test_data

      data = await sprints.afetch(3590800)

      assert 3590800 in data
      assert isinstance(data[3590800], ZPRaceSprint)
      # asdict() returns typed field names
      result = data[3590800].asdict()
      assert 'race_id' in result
      assert 'data' in result
      assert len(result['data']) == 2  # Two sprints
      mock_primes_afetch.assert_called_once_with(3590800)
