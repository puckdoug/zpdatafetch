"""Live tests for ZRCategoriesFetch that make real API calls to zwiftracing.app."""

import pytest

from zrdatafetch import ZRCategories, ZRCategoriesFetch


@pytest.mark.live
def test_live_zrcategories_fetch():
  """Test synchronous fetch of the vELO2 category ranges."""
  fetcher = ZRCategoriesFetch()
  categories = fetcher.fetch()

  assert isinstance(categories, ZRCategories)
  assert categories.scale == '1-1000'
  assert len(categories.categories) == 10
  assert categories.categories[0].max is None


@pytest.mark.live
@pytest.mark.anyio
async def test_live_zrcategories_afetch():
  """Test asynchronous fetch of the vELO2 category ranges."""
  fetcher = ZRCategoriesFetch()
  categories = await fetcher.afetch()

  assert isinstance(categories, ZRCategories)
  assert categories.scale == '1-1000'
  assert len(categories.categories) == 10
