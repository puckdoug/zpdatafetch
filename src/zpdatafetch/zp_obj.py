import json
from typing import Any, Dict


class ZP_obj:
  def __init__(self) -> None:
    self.raw: dict[Any, Any] = {}
    self.verbose: bool = False

  def __str__(self) -> str:
    return str(self.raw)

  def json(self) -> str:
    return json.JSONEncoder(indent=2).encode(self.raw)

  def asdict(self) -> dict[Any, Any]:
    return self.raw
