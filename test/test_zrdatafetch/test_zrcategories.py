"""Tests for ZRCategories dataclass parsing."""

import json
from pathlib import Path

import pytest

from zrdatafetch.zrcategories import ZRCategories, ZRCategoriesEntry

FIXTURE_PATH = Path(__file__).parent.parent / 'fixtures' / 'zr_categories.json'


@pytest.fixture
def categories_data() -> dict:
  """Load categories fixture data."""
  with open(FIXTURE_PATH, encoding='utf-8') as f:
    return json.load(f)


@pytest.fixture
def categories(categories_data: dict) -> ZRCategories:
  """Create ZRCategories from fixture data."""
  return ZRCategories.from_dict(categories_data)


class TestZRCategoriesBasic:
  """Test parsing of the live response shape."""

  def test_scale(self, categories: ZRCategories) -> None:
    assert categories.scale == '1-1000'

  def test_entry_count(self, categories: ZRCategories) -> None:
    assert len(categories.categories) == 10

  def test_diamond_top_category_max_is_none(
    self, categories: ZRCategories,
  ) -> None:
    diamond = categories.categories[0]
    assert diamond.number == 1
    assert diamond.name == 'Diamond'
    assert diamond.min == 920
    assert diamond.max is None

  def test_copper_bottom_category(self, categories: ZRCategories) -> None:
    copper = categories.categories[-1]
    assert copper.number == 10
    assert copper.name == 'Copper'
    assert copper.min == 0
    assert copper.max == 359

  def test_ruby_range(self, categories: ZRCategories) -> None:
    ruby = categories.categories[1]
    assert (ruby.min, ruby.max) == (840, 919)


class TestZRCategoriesEmpty:
  """Test empty instantiation and missing-key defaults."""

  def test_empty_instantiation(self) -> None:
    obj = ZRCategories()
    assert obj.scale == ''
    assert obj.categories == []

  def test_entry_empty_instantiation(self) -> None:
    obj = ZRCategoriesEntry()
    assert obj.number == 0
    assert obj.name == ''
    assert obj.min == 0
    assert obj.max is None

  def test_missing_categories_key(self) -> None:
    obj = ZRCategories.from_dict({'scale': '1-1000'})
    assert obj.scale == '1-1000'
    assert obj.categories == []

  def test_non_dict_entries_skipped(self) -> None:
    obj = ZRCategories.from_dict(
      {'scale': '1-1000', 'categories': ['bad', {'number': 1}]},
    )
    assert len(obj.categories) == 1
    assert obj.categories[0].number == 1

  def test_categories_not_a_list(self) -> None:
    obj = ZRCategories.from_dict({'scale': 's', 'categories': 'oops'})
    assert obj.categories == []


class TestZRCategoriesEntryParsing:
  """Test entry-level parsing."""

  def test_max_missing_is_none(self) -> None:
    entry = ZRCategoriesEntry.from_dict({'number': 1, 'name': 'X', 'min': 5})
    assert entry.max is None

  def test_max_null_is_none(self) -> None:
    entry = ZRCategoriesEntry.from_dict(
      {'number': 1, 'name': 'X', 'min': 5, 'max': None},
    )
    assert entry.max is None

  def test_string_numbers_parsed(self) -> None:
    entry = ZRCategoriesEntry.from_dict(
      {'number': '2', 'name': 'Y', 'min': '10', 'max': '19'},
    )
    assert entry.number == 2
    assert entry.min == 10
    assert entry.max == 19

  def test_unknown_keys_in_extra(self) -> None:
    entry = ZRCategoriesEntry.from_dict({'number': 1, 'colour': 'red'})
    assert entry.extras() == {'colour': 'red'}
    assert entry.excluded() == {}


class TestZRCategoriesFieldClassification:
  """Test _extra / _excluded handling."""

  def test_unknown_top_level_key_in_extra(self, categories_data) -> None:
    data = dict(categories_data)
    data['newField'] = {'a': 1}
    obj = ZRCategories.from_dict(data)
    assert 'newField' in obj.extras()
    assert obj.excluded() == {}

  def test_known_keys_not_in_extra(self, categories: ZRCategories) -> None:
    extras = categories.extras()
    assert 'scale' not in extras
    assert 'categories' not in extras


class TestZRCategoriesAsDict:
  """Test asdict()."""

  def test_asdict_shape(self, categories: ZRCategories) -> None:
    d = categories.asdict()
    assert set(d) == {'scale', 'categories'}
    assert d['scale'] == '1-1000'
    assert len(d['categories']) == 10
    assert d['categories'][0] == {
      'number': 1, 'name': 'Diamond', 'min': 920, 'max': None,
    }

  def test_asdict_excludes_private(self, categories: ZRCategories) -> None:
    d = categories.asdict()
    assert '_extra' not in d
    assert '_excluded' not in d

  def test_entry_asdict_excludes_private(self) -> None:
    entry = ZRCategoriesEntry.from_dict({'number': 1, 'zzz': 2})
    d = entry.asdict()
    assert '_extra' not in d
    assert '_excluded' not in d


class TestZRCategoriesRepr:
  """Test repr."""

  def test_repr_summary(self, categories: ZRCategories) -> None:
    r = repr(categories)
    assert r.startswith('ZRCategories(')
    assert "'1-1000'" in r
    assert 'categories=10' in r
