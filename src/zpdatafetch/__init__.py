# Core imports
from zpdatafetch.async_zp import AsyncZP
from zpdatafetch.config import Config
from zpdatafetch.cyclist import Cyclist
from zpdatafetch.logging_config import setup_logging
from zpdatafetch.primes import Primes
from zpdatafetch.result import Result
from zpdatafetch.signup import Signup
from zpdatafetch.sprints import Sprints
from zpdatafetch.team import Team
from zpdatafetch.zp import (
  ZP,
  ZPAuthenticationError,
  ZPConfigError,
  ZPNetworkError,
)

# Backwards compatibility aliases for async classes
# Note: These classes now support both sync (fetch) and async (afetch) methods
AsyncCyclist = Cyclist
AsyncPrimes = Primes
AsyncResult = Result
AsyncSignup = Signup
AsyncTeam = Team

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
  'ZPAuthenticationError',
  'ZPNetworkError',
  'ZPConfigError',
  'setup_logging',
  # Asynchronous API
  'AsyncZP',
  'AsyncCyclist',  # Alias for Cyclist (supports both sync and async)
  'AsyncPrimes',  # Alias for Primes (supports both sync and async)
  'AsyncResult',  # Alias for Result (supports both sync and async)
  'AsyncSignup',  # Alias for Signup (supports both sync and async)
  'AsyncTeam',  # Alias for Team (supports both sync and async)
]
