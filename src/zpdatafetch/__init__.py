# Core imports
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.config import Config
from zpdatafetch.logging_config import setup_logging
from zpdatafetch.zp import ZP
from zpdatafetch.zpcyclist import ZPCyclist
from zpdatafetch.zpcyclistfetch import ZPCyclistFetch
from zpdatafetch.zpleague import ZPLeague
from zpdatafetch.zpleaguefetch import ZPLeagueFetch
from zpdatafetch.zpprime import ZPPrime, ZPPrimeResult, ZPPrimeSegment
from zpdatafetch.zpprimesfetch import ZPPrimesFetch
from zpdatafetch.zpracefinish import ZPRaceFinish
from zpdatafetch.zpracelog import ZPRacelog
from zpdatafetch.zpraceresult import ZPRaceResult, ZPRiderFinish
from zpdatafetch.zpracesignup import ZPRaceSignup, ZPRiderSignup
from zpdatafetch.zpracesprint import ZPRaceSprint, ZPRiderSprint
from zpdatafetch.zpresultfetch import ZPResultFetch
from zpdatafetch.zpsignupfetch import ZPSignupFetch
from zpdatafetch.zpsprintsfetch import ZPSprintsFetch
from zpdatafetch.zpteam import ZPTeam, ZPTeamMember
from zpdatafetch.zpteamfetch import ZPTeamFetch

# Backwards compatibility aliases
RaceFinish = ZPRaceFinish
Racelog = ZPRacelog

# Backwards compatibility aliases for main fetcher classes
Cyclist = ZPCyclistFetch
Result = ZPResultFetch
Team = ZPTeamFetch
Signup = ZPSignupFetch
League = ZPLeagueFetch
Primes = ZPPrimesFetch
Sprints = ZPSprintsFetch

__all__ = [
  # Fetcher classes
  'ZP',
  'AsyncZP',
  'ZPCyclistFetch',
  'ZPPrimesFetch',
  'ZPResultFetch',
  'ZPSprintsFetch',
  'ZPSignupFetch',
  'ZPTeamFetch',
  'ZPLeagueFetch',
  'Config',
  'setup_logging',
  # Data classes
  'ZPCyclist',
  'ZPLeague',
  'ZPPrime',
  'ZPPrimeResult',
  'ZPPrimeSegment',
  'ZPRaceFinish',
  'ZPRacelog',
  'ZPRaceResult',
  'ZPRaceSignup',
  'ZPRaceSprint',
  'ZPRiderFinish',
  'ZPRiderSignup',
  'ZPRiderSprint',
  'ZPTeam',
  'ZPTeamMember',
  # Backwards compatibility aliases
  'RaceFinish',
  'Racelog',
  'Cyclist',
  'Result',
  'Team',
  'Signup',
  'League',
  'Primes',
  'Sprints',
]
