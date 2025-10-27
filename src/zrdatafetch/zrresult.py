import http.client
import json
import sys
from argparse import ArgumentParser
from pprint import pprint
from typing import ClassVar, Optional

from pydantic import BaseModel, PrivateAttr

SITE: str = 'zwift-ranking.herokuapp.com'
PATH: str = '/public/results'

sys.path.append('./etc')
try:
  from credentials import header
except Exception as e:
  print(e)  # noqa: T201


# ===============================================================================
class ZRRiderResult(BaseModel):
  _verbose: bool = PrivateAttr(default=False)
  category: str = None
  gap: float | None = 0.0
  position: int = 0
  positionInCategory: int = 0  # noqa: N815 - mixed case
  rating: float | None = 0.0
  ratingBefore: float | None = 0.0  # noqa: N815 - mixed case
  ratingDelta: float | None = 0.0  # noqa: N815 - mixed case
  riderId: int = 0  # noqa: N815 - mixed case
  time: float = 0.0


# ===============================================================================
class ZRResult(BaseModel):
  race_id: int = 0
  result: list[ZRRiderResult] = []
  _race: str = PrivateAttr(default=None)
  _verbose: bool = PrivateAttr(default=False)

  # make connection a class variable to allow reuse when fetching multiple IDs
  conn: ClassVar[http.client.HTTPSConnection] = http.client.HTTPSConnection(SITE)

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if self.race_id != 0:
      self.fetch()

  # -------------------------------------------------------------------------------
  def verbose(self, *args: bool) -> bool:
    for arg in args:
      self._verbose = arg
    return self._verbose

  # -------------------------------------------------------------------------------
  def fetch(self):
    ZRResult.conn.request('GET', f'{PATH}/{self.race_id}', headers=header)
    data = ZRResult.conn.getresponse().read()

    try:
      self._race = json.loads(data.decode('ascii'))
    except json.JSONDecodeError as e:
      print(f'JSON decoding error: {e}')

    try:
      for rider in self._race:
        rr = ZRRiderResult(**rider)
        self.result.append(rr)
    except Exception as e:
      print(f'parse failed {e} for {rider}')

  # -------------------------------------------------------------------------------
  def alldata(self):
    pprint(self.dict())


# ===============================================================================
def main():
  p = ArgumentParser(description='module to fetch results from Zwiftrace')
  p.add_argument(
    '--verbose',
    '-v',
    action='store_const',
    const=True,
    help='produce verbose results',
  )
  p.add_argument(
    '--alldata',
    '-a',
    action='store_const',
    const=True,
    help='print all returned data for a race',
  )
  p.add_argument('race_id', nargs='+', help='list of zwift race IDs to look up')
  args = p.parse_args()

  for zid in args.race_id:
    zr = ZRResult(race_id=zid)
    if args.verbose:
      zr.verbose(True)

    if args.alldata:
      zr.alldata()

    if args.verbose:
      pprint(zr.dict())


# ===============================================================================
if __name__ == '__main__':
  main()
