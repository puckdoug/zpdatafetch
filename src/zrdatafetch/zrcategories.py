"""Pure dataclasses for Zwiftracing vELO2 category ranges.

This module provides dataclasses for representing the vELO2 category
ranges without any fetch logic. Fetching is handled by ZRCategoriesFetch.
"""

from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, overload

from zrdatafetch.logging_config import get_logger
from zrdatafetch.zr_utils import safe_int, safe_str

logger = get_logger(__name__)


@dataclass(slots=True)
class ZRvELOCategory:
  """Single vELO2 category range.

  Attributes:
    number: Category number (1 = highest)
    name: Category name (e.g. 'Diamond', 'Copper')
    min: Minimum vELO2 rating for this category (inclusive)
    max: Maximum vELO2 rating for this category (inclusive);
      None for the top category (no upper bound)
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
  """

  number: int = 0
  name: str = ''
  min: int = 0
  max: int | None = None

  # Field classification
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRvELOCategory':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing category data

    Returns:
      ZRvELOCategory instance with parsed fields
    """
    known_fields = {'number', 'name', 'min', 'max'}
    recognized_but_excluded: set[str] = set()

    try:
      raw_max = data.get('max')
      max_value: int | None = None if raw_max is None else safe_int(raw_max)

      excluded = {}
      extra = {}
      for key, value in data.items():
        if key not in known_fields:
          if key in recognized_but_excluded:
            excluded[key] = value
          else:
            extra[key] = value

      return cls(
        number=safe_int(data.get('number')),
        name=safe_str(data.get('name')),
        min=safe_int(data.get('min')),
        max=max_value,
        _excluded=excluded,
        _extra=extra,
      )
    except (KeyError, TypeError, ValueError) as e:
      logger.warning(f'Error parsing category entry data: {e}')
      return cls()

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with all public attributes
    """
    result = asdict(self)
    result.pop('_extra', None)
    result.pop('_excluded', None)
    return result

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)


@dataclass(slots=True)
class ZRCategories:
  """vELO2 category ranges from the Zwiftracing API.

  Container behavior:
    iter(categories) yields entries in API order (index 0 = Diamond)
    categories['Silver'] returns the entry with that exact name
    'Silver' in categories, len(categories)
    categories[0], categories[0:3] positional access

  Attributes:
    scale: Human-readable rating scale label (e.g. '1-1000')
    categories: Ordered list of category ranges (1 = highest)
    _excluded: Recognized but not explicitly handled fields
    _extra: Unknown/new fields from API changes
  """

  scale: str = ''
  categories: list[ZRvELOCategory] = field(default_factory=list)

  # Field classification
  _excluded: dict[str, Any] = field(default_factory=dict, repr=False)
  _extra: dict[str, Any] = field(default_factory=dict, repr=False)

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> 'ZRCategories':
    """Create instance from API response dict.

    Args:
      data: Dictionary containing the categories response

    Returns:
      ZRCategories instance with parsed fields and entries
    """
    known_fields = {'scale', 'categories'}
    recognized_but_excluded: set[str] = set()

    entries: list[ZRvELOCategory] = []
    raw_entries = data.get('categories') or []
    if not isinstance(raw_entries, list):
      logger.warning(
        f'Expected list for categories, got {type(raw_entries).__name__}',
      )
      raw_entries = []
    for entry_data in raw_entries:
      if not isinstance(entry_data, dict):
        logger.warning('Skipping malformed category entry (not a dict)')
        continue
      try:
        entries.append(ZRvELOCategory.from_dict(entry_data))
      except (KeyError, TypeError, ValueError) as e:
        logger.warning(f'Skipping malformed category entry: {e}')
        continue

    excluded = {}
    extra = {}
    for key, value in data.items():
      if key not in known_fields:
        if key in recognized_but_excluded:
          excluded[key] = value
        else:
          extra[key] = value

    return cls(
      scale=safe_str(data.get('scale')),
      categories=entries,
      _excluded=excluded,
      _extra=extra,
    )

  def asdict(self) -> dict[str, Any]:
    """Return dictionary representation excluding private attributes.

    Returns:
      Dictionary with scale and category entries
    """
    return {
      'scale': self.scale,
      'categories': [entry.asdict() for entry in self.categories],
    }

  def excluded(self) -> dict[str, Any]:
    """Return all excluded fields.

    Returns:
      Dictionary of excluded fields
    """
    return dict(self._excluded)

  def extras(self) -> dict[str, Any]:
    """Return all unknown fields.

    Returns:
      Dictionary of unknown fields
    """
    return dict(self._extra)

  def __len__(self) -> int:
    """Return the number of category entries.

    Returns:
      Number of entries
    """
    return len(self.categories)

  @overload
  def __getitem__(self, key: int) -> ZRvELOCategory: ...
  @overload
  def __getitem__(self, key: slice) -> Sequence[ZRvELOCategory]: ...
  @overload
  def __getitem__(self, key: str) -> ZRvELOCategory: ...

  def __getitem__(
    self, key: int | slice | str,
  ) -> ZRvELOCategory | Sequence[ZRvELOCategory]:
    """Access a category by position or by exact name.

    Args:
      key: Integer index, slice, or exact case-sensitive category name

    Returns:
      ZRvELOCategory, or a sequence of entries for a slice

    Raises:
      KeyError: If a string name matches no category
      IndexError: If an integer index is out of range
    """
    if isinstance(key, str):
      for entry in self.categories:
        if entry.name == key:
          return entry
      raise KeyError(key)
    return self.categories[key]

  def __iter__(self) -> Iterator[ZRvELOCategory]:
    """Iterate over category entries in API order.

    Returns:
      Iterator over ZRvELOCategory objects (index 0 = Diamond)
    """
    return iter(self.categories)

  def __contains__(self, key: object) -> bool:
    """Check whether a category name is present.

    Args:
      key: Category name to look for

    Returns:
      True if a category with that exact name exists
    """
    return any(entry.name == key for entry in self.categories)
