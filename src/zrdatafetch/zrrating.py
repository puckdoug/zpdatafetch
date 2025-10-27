import http.client
import json
import sys
from argparse import ArgumentParser
from contextlib import suppress
from pprint import pprint
from typing import ClassVar

import dateparser
from pydantic import BaseModel, PrivateAttr

SITE: str = 'zwift-ranking.herokuapp.com'
PATH: str = '/public/riders'

sys.path.append('./etc')
try:
  from credentials import header
except Exception as e:
  print(e)


# ===============================================================================


class ZRRating(BaseModel):
  zwift_id: int = 0
  epoch: int = -1
  name: str = 'Nobody'
  gender: str = 'M'
  current_rating: float = 0.0
  current_rank: str = 'Unranked'
  max30_rating: float = 0.0
  max30_rank: str = 'Unranked'
  max90_rating: float = 0.0
  max90_rank: str = 'Unranked'
  drs_rating: float = 0.0
  drs_rank: str = 'Unranked'
  zrcs: float = 0.0
  source: str = 'none'
  _verbose: bool = PrivateAttr(default=False)
  _raw: str = PrivateAttr()
  _rider: str = PrivateAttr()

  # make connection a class variable to allow reuse when fetching multiple IDs
  conn: ClassVar[http.client.HTTPSConnection] = http.client.HTTPSConnection(SITE)

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if self.zwift_id != 0:
      self.fetch()

  # -------------------------------------------------------------------------------
  def verbose(self, *args: bool) -> bool:
    for arg in args:
      self._verbose = arg
    return self._verbose

  # -------------------------------------------------------------------------------
  def fetch(self):
    if self.epoch >= 0:
      ZRRating.conn.request(
        'GET',
        f'{PATH}/{self.zwift_id}/{self.epoch}',
        headers=header,
      )
    else:
      ZRRating.conn.request('GET', f'{PATH}/{self.zwift_id}', headers=header)

    data = ZRRating.conn.getresponse().read()
    self._raw = data.decode('UTF-8')
    try:
      self._rider = json.loads(data)
    except Exception as e:
      print(e)
      return

    if self._rider is not None:
      if 'race' not in self._rider or 'name' not in self._rider:
        if 'message' in self._rider:
          print(self._rider['message'])
        else:
          print("Couldn't find name or race data")
      else:
        with suppress(Exception):  # just use defaults for fields that are empty
          self.name = self._rider['name']
          self.gender = self._rider['gender']
          self.zrcs = self._rider['power']['compoundScore']
          self.current_rating = self._rider['race']['current']['rating']
          self.current_rank = self._rider['race']['current']['mixed']['category']
          if self._rider['race']['max90']['rating'] is not None:
            self.max90_rating = self._rider['race']['max90']['rating']
          self.max90_rank = self._rider['race']['max90']['mixed']['category']
          if self._rider['race']['max30']['rating'] is not None:
            self.max30_rating = self._rider['race']['max30']['rating']
          self.max30_rank = self._rider['race']['max30']['mixed']['category']

        if self.max30_rank != 'Unranked':
          self.drs_rating = self.max30_rating
          self.drs_rank = self.max30_rank
          self.source = 'max30'
        elif self.max90_rank != 'Unranked':
          self.drs_rating = self.max90_rating
          self.drs_rank = self.max90_rank
          self.source = 'max90'
    elif self._verbose:
      print(f'Bad ID: {self.zwift_id}')

  # -------------------------------------------------------------------------------
  def raw(self):
    print(self._raw)

  # -------------------------------------------------------------------------------
  def alldata(self):
    pprint(self._rider)


# ===============================================================================
def main():
  p = ArgumentParser(description="module to fetch a rider's Zwiftrace ranking")
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
    help='print all returned data for a rider',
  )
  p.add_argument(
    '--raw',
    '-r',
    action='store_const',
    const=True,
    help='print the raw results returned by the server',
  )
  #  p.add_argument('--zrcs', '-z', action='store_const', const=True,
  #    help='use zrcs in place of max 30 days if max is empty')
  p.add_argument(
    '--date',
    '-d',
    nargs='+',
    help='fetch as of a particular date/time - must be quoted',
  )
  p.add_argument('zwift_id', nargs='+', help='list of zwift IDs to look up')
  args = p.parse_args()

  for zid in args.zwift_id:
    if args.date:
      d = ' '.join(args.date)
      as_of = dateparser.parse(d).strftime('%s')
      zr = ZRRating(zwift_id=zid, epoch=as_of)
    else:
      zr = ZRRating(zwift_id=zid)
    if args.verbose:
      zr.verbose(True)
    #    if args.zrcs is True:
    #      zr.zrcs_for_max30()

    if args.alldata:
      zr.alldata()

    if args.raw:
      zr.raw()
      sys.exit(0)

    if args.verbose:
      pprint(zr.dict())


# ===============================================================================
if __name__ == '__main__':
  main()
