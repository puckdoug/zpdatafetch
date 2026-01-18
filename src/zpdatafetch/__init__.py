# Core imports
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.config import Config
from zpdatafetch.cyclist import Cyclist
from zpdatafetch.league import League
from zpdatafetch.logging_config import setup_logging
from zpdatafetch.primes import Primes
from zpdatafetch.result import Result
from zpdatafetch.signup import Signup
from zpdatafetch.sprints import Sprints
from zpdatafetch.team import Team
from zpdatafetch.zp import ZP
from zpdatafetch.zpcyclist import ZPCyclist
from zpdatafetch.zpleague import ZPLeague
from zpdatafetch.zpprime import ZPPrime, ZPPrimeSegment
from zpdatafetch.zpracefinish import ZPRaceFinish
from zpdatafetch.zpracelog import ZPRacelog
from zpdatafetch.zpraceresult import ZPRaceResult, ZPRiderFinish
from zpdatafetch.zpracesignup import ZPRaceSignup, ZPRiderSignup
from zpdatafetch.zpracesprint import ZPRaceSprint, ZPRiderSprint
from zpdatafetch.zpteam import ZPTeam, ZPTeamMember

# Backwards compatibility aliases
RaceFinish = ZPRaceFinish
Racelog = ZPRacelog

# Backwards compatibility aliases for async classes
# Note: These classes now support both sync (fetch) and async (afetch) methods
AsyncCyclist = Cyclist
AsyncPrimes = Primes
AsyncResult = Result
AsyncSignup = Signup
AsyncTeam = Team
AsyncLeague = League

__all__ = [
  # Synchronous API
  'ZP',
  'Cyclist',
  'Primes',
  'Result',
  'Sprints',
  'Config',
  'Signup',
  'Team',
  'League',
  'setup_logging',
  # Race data classes
  'ZPCyclist',
  'ZPLeague',
  'ZPPrime',
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
  'RaceFinish',  # Backwards compatibility alias
  'Racelog',  # Backwards compatibility alias
  # Asynchronous API
  'AsyncZP',
  'AsyncCyclist',  # Alias for Cyclist (supports both sync and async)
  'AsyncPrimes',  # Alias for Primes (supports both sync and async)
  'AsyncResult',  # Alias for Result (supports both sync and async)
  'AsyncSignup',  # Alias for Signup (supports both sync and async)
  'AsyncTeam',  # Alias for Team (supports both sync and async)
  'AsyncLeague',  # Alias for League (supports both sync and async)
]
