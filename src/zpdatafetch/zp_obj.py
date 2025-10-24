import json


class ZP_obj:
  def __init__(self):
    self.raw = {}
    self.verbose = False

  def __str__(self):
    return str(self.raw)

  def json(self):
    return json.JSONEncoder(indent=2).encode(self.raw)

  def asdict(self):
    return self.raw
