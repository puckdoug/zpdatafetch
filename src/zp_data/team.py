from argparse import ArgumentParser
from zp_data.zp import ZP


# ===============================================================================
class Team:
  # "https://zwiftpower.com/cache3/teams/{team_id}_riders.json"
  _url = 'https://zwiftpower.com/cache3/teams/'
  _url_end = '_riders.json'
  raw = None
  verbose = False

  # -------------------------------------------------------------------------------
  def fetch(self, *team_id):
    zp = ZP()
    content = {}
    if self.verbose:
      zp.verbose = True

    for t in team_id:
      url = f'{self._url}{t}{self._url_end}'
      if zp.verbose:
        print(f'fetching: {url}')
      content[t] = zp.fetch_json(url)

    self.raw = content

    return self.raw


# ===============================================================================
def main():
  p = ArgumentParser(
    description='Module for fetching cyclist data using the Zwifpower API'
  )
  p.add_argument(
    '--verbose',
    '-v',
    action='store_const',
    const=True,
    help='provide feedback while running',
  )
  p.add_argument(
    '--raw', action='store_const', const=True, help='print all returned data'
  )
  p.add_argument(
    '--archive',
    action='store_const',
    const=True,
    help='archive signups to archive/ directory',
  )
  p.add_argument('team_id', type=int, nargs='+', help='a list of team_ids')
  args = p.parse_args()

  x = Team()

  if args.verbose:
    x.verbose = True

  team = x.fetch(*args.team_id)

  if args.raw:
    print(x.raw)

  if args.archive:
    ZP.archive('team', team)


# ===============================================================================
if __name__ == '__main__':
  main()
