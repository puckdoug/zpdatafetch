import http.client
import json
import sys
import time
from argparse import ArgumentParser
from pprint import pprint
from typing import ClassVar

import chardet
from pydantic import BaseModel, PrivateAttr

SITE: str = 'zwift-ranking.herokuapp.com'
PATH: str = '/public/clubs'

sys.path.append('./etc')
try:
  from credentials import header
except Exception as e:
  print(e)  # noqa: T201


# ===============================================================================


class ZRTeam(BaseModel):
  team_id: int = 0
  first_rider_id: int = 0
  team_name: str = ''
  riders: list | None = []
  _url: str = PrivateAttr(default=f'https://{SITE}{PATH}/{team_id}')
  _verbose: bool = PrivateAttr(default=False)
  _response: http.client.HTTPResponse = PrivateAttr()
  _raw: str = PrivateAttr()
  _team: str = PrivateAttr()

  # make connection a class variable to allow reuse when fetching multiple IDs
  conn: ClassVar[http.client.HTTPSConnection] = http.client.HTTPSConnection(SITE)

  def __init__(self, **kwargs):
    self._team = None
    super().__init__(**kwargs)
    if self.team_id != 0:
      self.fetch()

  # -------------------------------------------------------------------------------
  def verbose(self, *args: bool) -> bool:
    for arg in args:
      self._verbose = arg
    return self._verbose

  # -------------------------------------------------------------------------------
  def url(self) -> str:
    return self._url

  # -------------------------------------------------------------------------------
  def fetch(self):
    while True:
      self._url = f'{PATH}/{self.team_id}/{self.first_rider_id}'
      if self._verbose is True:
        print(f'Fetching: {self._url}')

      ZRTeam.conn.request('GET', self._url, headers=header)
      self._response = ZRTeam.conn.getresponse()
      if self._response.status != 200:
        print(self._response.status, self._response.reason)
        sys.exit(0)

      self._raw = self._response.read()

      enc = chardet.detect(self._raw)['encoding']
      try:
        self._team = json.loads(self._raw.decode(encoding=enc))
      except Exception as e:
        print(e)
        sys.exit(1)

      if self._team is not None:
        self.team_name = self._team['name']
        r = {}
        for rider in self._team['riders']:
          r = {}
          r['zwift_id'] = rider['riderId']
          r['name'] = rider['name']
          r['gender'] = rider['gender']
          r['height'] = rider['height']
          r['weight'] = rider['weight']
          try:
            r['current_mixed_category'] = rider['race']['current']['mixed']['category']
          except KeyError:
            r['current_mixed_category'] = ''
          try:
            r['current_womens_category'] = rider['race']['current']['womens'][
              'category'
            ]
          except KeyError:
            r['current_womens_category'] = ''
          try:
            r['current_rating'] = rider['race']['current']['rating']
          except KeyError:
            r['current_rating'] = 0.0
          try:
            r['max30_mixed_category'] = rider['race']['max30']['mixed']['category']
          except KeyError:
            r['max30_mixed_category'] = ''
          try:
            r['max30_womens_category'] = rider['race']['max30']['womens']['category']
          except KeyError:
            r['max30_womens_category'] = ''
          try:
            r['max30_rating'] = rider['race']['max30']['rating']
          except KeyError:
            r['max30_rating'] = 0.0
          try:
            r['max90_mixed_category'] = rider['race']['max90']['mixed']['category']
          except KeyError:
            r['max90_mixed_category'] = ''
          try:
            r['max90_womens_category'] = rider['race']['max90']['womens']['category']
          except KeyError:
            r['max90_womens_category'] = ''
          try:
            r['max90_rating'] = rider['race']['max90']['rating']
          except KeyError:
            r['max90_rating'] = 0.0
          try:
            r['power_AWC'] = rider['power']['AWC']
          except KeyError:
            r['power_AWC'] = 0.0
          try:
            r['power_CP'] = rider['power']['CP']
          except KeyError:
            r['power_CP'] = 0.0
          try:
            r['power_CS'] = rider['power']['compoundScore']
          except KeyError:
            r['power_CS'] = 0.0
          try:
            r['power_w120'] = rider['power']['w120']
          except KeyError:
            r['power_w120'] = 0
          try:
            r['power_w1200'] = rider['power']['w1200']
          except KeyError:
            r['power_w1200'] = 0
          try:
            r['power_w15'] = rider['power']['w15']
          except KeyError:
            r['power_w15'] = 0
          try:
            r['power_w30'] = rider['power']['w30']
          except KeyError:
            r['power_w30'] = 0
          try:
            r['power_w300'] = rider['power']['w300']
          except KeyError:
            r['power_w300'] = 0
          try:
            r['power_w5'] = rider['power']['w5']
          except KeyError:
            r['power_w5'] = 0
          try:
            r['power_w60'] = rider['power']['w60']
          except KeyError:
            r['power_w60'] = 0
          try:
            r['power_wkg120'] = rider['power']['wkg120']
          except KeyError:
            r['power_wkg120'] = 0.0
          try:
            r['power_wkg1200'] = rider['power']['wkg1200']
          except KeyError:
            r['power_wkg1200'] = 0.0
          try:
            r['power_wkg15'] = rider['power']['wkg15']
          except KeyError:
            r['power_wkg15'] = 0.0
          try:
            r['power_wkg30'] = rider['power']['wkg30']
          except KeyError:
            r['power_wkg30'] = 0.0
          try:
            r['power_wkg300'] = rider['power']['wkg300']
          except KeyError:
            r['power_wkg300'] = 0.0
          try:
            r['power_wkg5'] = rider['power']['wkg5']
          except KeyError:
            r['power_wkg5'] = 0.0
          try:
            r['power_wkg60'] = rider['power']['wkg60']
          except KeyError:
            r['power_wkg60'] = 0.0
          self.riders.append(r)

          if self.verbose:
            print(f'{r["zwift_id"]} {r["name"]}')

        try:
          if self.first_rider_id == r['zwift_id']:
            return
          self.first_rider_id = r['zwift_id'] + 1
          time.sleep(5)
        except KeyError:
          return

  # -------------------------------------------------------------------------------
  def raw(self):
    enc = chardet.detect(self._raw)['encoding']
    print(self._raw.decode(encoding=enc))

  # -------------------------------------------------------------------------------
  def alldata(self):
    pprint(self)


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
    '--raw',
    '-r',
    action='store_const',
    const=True,
    help='print raw data returned for a rider',
  )
  p.add_argument(
    '--url',
    '-u',
    action='store_const',
    const=True,
    help='print the URL that will be called',
  )
  p.add_argument(
    '--alldata',
    '-a',
    action='store_const',
    const=True,
    help='print all returned data for a rider',
  )
  p.add_argument('team_id', help='Team ID to look up')
  args = p.parse_args()

  if args.verbose:
    team = ZRTeam(team_id=args.team_id, verbose=True)
  else:
    team = ZRTeam(team_id=args.team_id, verbose=False)

  if args.url:
    print(team.url())
    sys.exit(0)

  if args.raw:
    team.raw()

  if args.alldata:
    team.alldata()


# ===============================================================================
if __name__ == '__main__':
  main()
