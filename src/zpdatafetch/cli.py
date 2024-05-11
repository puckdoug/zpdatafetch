import sys
from argparse import ArgumentParser
from zpdatafetch import Config, Cyclist, Primes, Result, Signup, Team


# ===============================================================================
def main():
  desc = """
Module for fetching zwiftpower data using the Zwifpower API
  """
  p = ArgumentParser(description=desc)
  p.add_argument(
    '-v',
    '--verbose',
    action='store_const',
    const=True,
    help='provide feedback while running',
  )
  p.add_argument(
    'cmd',
    help='which command to run',
    nargs='?',
    choices=('config', 'cyclist', 'primes', 'result', 'signup', 'team'),
  )
  p.add_argument(
    'id', help='the id to search for, ignored for config', nargs='*'
  )
  args = p.parse_args()

  match args.cmd:
    case 'config':
      c = Config()
      c.setup()
      sys.exit(0)
    case 'cyclist':
      x = Cyclist()
    case 'primes':
      x = Primes()
    case 'result':
      x = Result()
    case 'signup':
      x = Signup()
    case 'team':
      x = Team()
    case _:
      sys.exit(0)

  if args.verbose:
    x.verbose = True
  x.fetch(*args.id)
  print(x.json())


# ===============================================================================
if __name__ == '__main__':
  sys.exit(main())
