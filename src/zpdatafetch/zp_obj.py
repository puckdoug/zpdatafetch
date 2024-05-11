import json


class ZP_obj:
  raw = {}
  verbose = False

  def __str__(self):
    return str(self.raw)

  def json(self):
    return json.JSONEncoder(indent=2).encode(self.raw)

  def asdict(self):
    return self.raw
