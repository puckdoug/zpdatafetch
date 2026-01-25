"""Zwift rider profile data fetching and management.

Provides access to rider profile information from Zwift's unofficial API
including demographics, statistics, and connected services.
"""

import json
from typing import Any

import httpx

from shared.exceptions import ConfigError, NetworkError
from shared.json_helpers import parse_json_safe
from zdatafetch.auth import ZwiftAuth
from zdatafetch.config import Config
from zdatafetch.logging_config import get_logger

logger = get_logger(__name__)


class ZwiftProfile:
  """Zwift rider profile data.

  Represents a single rider's profile with comprehensive information including
  personal details, statistics, connected services, and social data from
  Zwift's unofficial API.

  API Endpoint: GET https://us-or-rly101.zwift.com/api/profiles/{riderId}
  Documentation: https://github.com/strukturunion-mmw/zwift-api-documentation

  Synchronous usage:
      profile = ZwiftProfile()
      profile.fetch(550564)
      print(f"{profile.firstName} {profile.lastName}")
      print(f"FTP: {profile.ftp}w")
      print(profile)  # Pretty print all data

  Batch usage:
      profiles = ZwiftProfile.fetch_multiple(550564, 123456)
      for rider_id, profile in profiles.items():
          print(f"{profile.firstName}: {profile.ftp}w")

  Attributes:
      id: Rider ID
      firstName: First name
      lastName: Last name
      ftp: Functional Threshold Power (watts)
      weight: Weight in grams
      height: Height in centimeters
      ... and all other profile fields accessible as attributes
  """

  BASE_URL = 'https://us-or-rly101.zwift.com'

  def __init__(self) -> None:
    """Initialize empty profile (no auth parameter).

    Credentials are loaded from Config at fetch time.
    """
    self._raw: str = ''  # Raw JSON response
    self._fetched: dict[str, Any] = {}  # Parsed data dict
    self.processed: dict = {}  # Reserved for future use

    # Profile fields (populated after fetch) - all fields from Zwift API
    # Identity
    self.id: int = 0
    self.publicId: str = ''
    self.firstName: str = ''
    self.lastName: str = ''
    self.male: bool = True
    self.imageSrc: str = ''
    self.imageSrcLarge: str = ''

    # Location & Settings
    self.countryAlpha3: str = ''
    self.countryCode: int = 0
    self.useMetric: bool = True
    self.preferredLanguage: str = ''
    self.location: str | None = None

    # Status
    self.riding: bool = False
    self.likelyInGame: bool = False
    self.worldId: int | None = None

    # Account Type
    self.playerType: str = ''
    self.playerTypeId: int = 0
    self.enrolledZwiftAcademy: bool = False

    # Connected Services
    self.connectedToStrava: bool = False
    self.connectedToTrainingPeaks: bool = False
    self.connectedToTodaysPlan: bool = False
    self.connectedToUnderArmour: bool = False
    self.connectedToWithings: bool = False
    self.connectedToFitbit: bool = False
    self.connectedToGarmin: bool = False
    self.connectedToRuntastic: bool = False
    self.connectedToZwiftCompanion: bool = False
    self.connectedToFacebookMessenger: bool = False
    self.stravaPremium: bool = False

    # Personal Data
    self.dob: str = ''
    self.emailAddress: str | None = None
    self.height: int = 0  # cm
    self.weight: int = 0  # grams
    self.ftp: int = 0  # watts

    # Power/Equipment
    self.powerSourceType: str | None = None
    self.powerSourceModel: str | None = None
    self.virtualBikeModel: str | None = None

    # Account Info
    self.createdOn: str = ''
    self.launchedGameClient: str | None = None
    self.source: str = ''
    self.origin: str | None = None
    self.b: bool = False
    self.bt: str | None = None
    self.profileChanges: bool = False
    self.profilePropertyChanges: str | None = None

    # Running Times
    self.runTime1miInSeconds: int | None = None
    self.runTime5kmInSeconds: int | None = None
    self.runTime10kmInSeconds: int | None = None
    self.runTimeHalfMarathonInSeconds: int | None = None
    self.runTimeFullMarathonInSeconds: int | None = None

    # Organizations
    self.cyclingOrganization: str | None = None
    self.licenseNumber: str | None = None

    # Other
    self.avantlinkId: str | None = None
    self.bigCommerceId: str | None = None
    self.marketingConsent: str | None = None
    self.mixpanelDistinctId: str | None = None
    self.userAgent: str | None = None
    self.address: dict[str, Any] | None = None

    # Achievement & Stats
    self.achievementLevel: int = 0
    self.totalDistance: int = 0
    self.totalDistanceClimbed: int = 0
    self.totalTimeInMinutes: int = 0
    self.totalInKomJersey: int = 0
    self.totalInSprintersJersey: int = 0
    self.totalInOrangeJersey: int = 0
    self.totalWattHours: int = 0
    self.totalExperiencePoints: int = 0
    self.totalGold: int = 0

    # Running Stats
    self.runAchievementLevel: int = 0
    self.totalRunDistance: int = 0
    self.totalRunTimeInMinutes: int = 0
    self.totalRunExperiencePoints: int = 0
    self.totalRunCalories: int = 0

    # Social Metrics
    self.numberOfFolloweesInCommon: int = 0

  def fetch(self, rider_id: int) -> None:
    """Fetch profile data for a single rider.

    Loads credentials from Config, authenticates, fetches data,
    and populates instance attributes.

    Args:
        rider_id: Zwift rider ID

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails
        AuthenticationError: If authentication fails
    """
    # Load credentials from config
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(f'Fetching profile for rider {rider_id}')

    # Authenticate
    auth = ZwiftAuth(config.username, config.password)
    auth.login()

    # Fetch data
    url = f'{self.BASE_URL}/api/profiles/{rider_id}'
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    try:
      with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=30.0)

        if response.status_code == 404:
          raise NetworkError(f'Rider {rider_id} not found')
        if response.status_code != 200:
          raise NetworkError(
            f'Failed to fetch profile for rider {rider_id}: '
            f'HTTP {response.status_code} - {response.text}',
          )

        # Store raw response
        self._raw = response.text

        # Parse and populate attributes
        self._parse_response()
        logger.info(f'Successfully fetched profile for rider {rider_id}')

    except httpx.TimeoutException as e:
      raise NetworkError(
        f'Request timed out fetching profile for rider {rider_id}: {e}',
      ) from e
    except httpx.HTTPError as e:
      raise NetworkError(
        f'Network error fetching profile for rider {rider_id}: {e}',
      ) from e

  @classmethod
  def fetch_multiple(cls, *rider_ids: int) -> dict[int, 'ZwiftProfile']:
    """Fetch multiple riders, returning dict of profile objects.

    Args:
        *rider_ids: Zwift rider IDs to fetch

    Returns:
        Dictionary mapping rider IDs to ZwiftProfile objects

    Raises:
        ConfigError: If credentials not configured
        NetworkError: If API request fails

    Example:
        profiles = ZwiftProfile.fetch_multiple(550564, 123456, 789012)
        for rider_id, profile in profiles.items():
            print(f"{profile.firstName}: {profile.ftp}w")
    """
    if not rider_ids:
      logger.warning('No rider IDs provided for batch fetch')
      return {}

    # Load credentials once
    config = Config()
    config.load()

    if not config.username or not config.password:
      raise ConfigError(
        'Zwift credentials not found. Run "zdata config" to set up credentials.',
      )

    logger.debug(f'Fetching {len(rider_ids)} profiles in batch')

    # Authenticate once
    auth = ZwiftAuth(config.username, config.password)
    auth.login()
    token = auth.get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Fetch all profiles
    results = {}
    with httpx.Client() as client:
      for rider_id in rider_ids:
        try:
          url = f'{cls.BASE_URL}/api/profiles/{rider_id}'
          response = client.get(url, headers=headers, timeout=30.0)

          if response.status_code == 200:
            profile = cls()
            profile._raw = response.text
            profile._parse_response()
            results[rider_id] = profile
            logger.debug(f'Successfully fetched profile for rider {rider_id}')
          else:
            logger.warning(
              f'Failed to fetch rider {rider_id}: HTTP {response.status_code}',
            )
        except Exception as e:
          logger.error(f'Error fetching rider {rider_id}: {e}')
          continue

    logger.info(
      f'Successfully fetched {len(results)}/{len(rider_ids)} profiles in batch',
    )
    return results

  def _parse_response(self) -> None:
    """Parse raw JSON string into structured profile data.

    Populates instance attributes from parsed data.
    Flattens nested dictionaries (privacy, socialFacts, publicAttributes, competitionMetrics).
    """
    if not self._raw:
      logger.warning('No data to parse')
      return

    parsed = parse_json_safe(self._raw, context='profile')
    if not isinstance(parsed, dict):
      logger.error(
        f'Expected dict for profile data, got {type(parsed).__name__}'
      )
      return

    # Flatten nested dictionaries into the main _fetched dict
    flattened = {}
    for key, value in parsed.items():
      if key in (
        'privacy',
        'socialFacts',
        'publicAttributes',
        'competitionMetrics',
      ) and isinstance(value, dict):
        # Flatten nested dict by adding its keys to the top level
        for nested_key, nested_value in value.items():
          flattened[nested_key] = nested_value
      else:
        flattened[key] = value

    self._fetched = flattened

    # Populate all attributes from flattened data
    # Identity
    self.id = flattened.get('id', 0)
    self.publicId = flattened.get('publicId', '')
    self.firstName = flattened.get('firstName', '')
    self.lastName = flattened.get('lastName', '')
    self.male = flattened.get('male', True)
    self.imageSrc = flattened.get('imageSrc', '')
    self.imageSrcLarge = flattened.get('imageSrcLarge', '')

    # Location & Settings
    self.countryAlpha3 = flattened.get('countryAlpha3', '')
    self.countryCode = flattened.get('countryCode', 0)
    self.useMetric = flattened.get('useMetric', True)
    self.preferredLanguage = flattened.get('preferredLanguage', '')
    self.location = flattened.get('location')

    # Status
    self.riding = flattened.get('riding', False)
    self.likelyInGame = flattened.get('likelyInGame', False)
    self.worldId = flattened.get('worldId')

    # Account Type
    self.playerType = flattened.get('playerType', '')
    self.playerTypeId = flattened.get('playerTypeId', 0)
    self.enrolledZwiftAcademy = flattened.get('enrolledZwiftAcademy', False)

    # Connected Services
    self.connectedToStrava = flattened.get('connectedToStrava', False)
    self.connectedToTrainingPeaks = flattened.get(
      'connectedToTrainingPeaks', False
    )
    self.connectedToTodaysPlan = flattened.get('connectedToTodaysPlan', False)
    self.connectedToUnderArmour = flattened.get('connectedToUnderArmour', False)
    self.connectedToWithings = flattened.get('connectedToWithings', False)
    self.connectedToFitbit = flattened.get('connectedToFitbit', False)
    self.connectedToGarmin = flattened.get('connectedToGarmin', False)
    self.connectedToRuntastic = flattened.get('connectedToRuntastic', False)
    self.connectedToZwiftCompanion = flattened.get(
      'connectedToZwiftCompanion', False
    )
    self.connectedToFacebookMessenger = flattened.get(
      'connectedToFacebookMessenger',
      False,
    )
    self.stravaPremium = flattened.get('stravaPremium', False)

    # Personal Data
    self.dob = flattened.get('dob', '')
    self.emailAddress = flattened.get('emailAddress')
    self.height = flattened.get('height', 0)
    self.weight = flattened.get('weight', 0)
    self.ftp = flattened.get('ftp', 0)

    # Power/Equipment
    self.powerSourceType = flattened.get('powerSourceType')
    self.powerSourceModel = flattened.get('powerSourceModel')
    self.virtualBikeModel = flattened.get('virtualBikeModel')

    # Account Info
    self.createdOn = flattened.get('createdOn', '')
    self.launchedGameClient = flattened.get('launchedGameClient')
    self.source = flattened.get('source', '')
    self.origin = flattened.get('origin')
    self.b = flattened.get('b', False)
    self.bt = flattened.get('bt')
    self.profileChanges = flattened.get('profileChanges', False)
    self.profilePropertyChanges = flattened.get('profilePropertyChanges')

    # Running Times
    self.runTime1miInSeconds = flattened.get('runTime1miInSeconds')
    self.runTime5kmInSeconds = flattened.get('runTime5kmInSeconds')
    self.runTime10kmInSeconds = flattened.get('runTime10kmInSeconds')
    self.runTimeHalfMarathonInSeconds = flattened.get(
      'runTimeHalfMarathonInSeconds'
    )
    self.runTimeFullMarathonInSeconds = flattened.get(
      'runTimeFullMarathonInSeconds'
    )

    # Organizations
    self.cyclingOrganization = flattened.get('cyclingOrganization')
    self.licenseNumber = flattened.get('licenseNumber')

    # Other
    self.avantlinkId = flattened.get('avantlinkId')
    self.bigCommerceId = flattened.get('bigCommerceId')
    self.marketingConsent = flattened.get('marketingConsent')
    self.mixpanelDistinctId = flattened.get('mixpanelDistinctId')
    self.userAgent = flattened.get('userAgent')
    self.address = flattened.get('address')

    # Achievement & Stats
    self.achievementLevel = flattened.get('achievementLevel', 0)
    self.totalDistance = flattened.get('totalDistance', 0)
    self.totalDistanceClimbed = flattened.get('totalDistanceClimbed', 0)
    self.totalTimeInMinutes = flattened.get('totalTimeInMinutes', 0)
    self.totalInKomJersey = flattened.get('totalInKomJersey', 0)
    self.totalInSprintersJersey = flattened.get('totalInSprintersJersey', 0)
    self.totalInOrangeJersey = flattened.get('totalInOrangeJersey', 0)
    self.totalWattHours = flattened.get('totalWattHours', 0)
    self.totalExperiencePoints = flattened.get('totalExperiencePoints', 0)
    self.totalGold = flattened.get('totalGold', 0)

    # Running Stats
    self.runAchievementLevel = flattened.get('runAchievementLevel', 0)
    self.totalRunDistance = flattened.get('totalRunDistance', 0)
    self.totalRunTimeInMinutes = flattened.get('totalRunTimeInMinutes', 0)
    self.totalRunExperiencePoints = flattened.get('totalRunExperiencePoints', 0)
    self.totalRunCalories = flattened.get('totalRunCalories', 0)

    # Social Metrics
    self.numberOfFolloweesInCommon = flattened.get(
      'numberOfFolloweesInCommon', 0
    )

    logger.debug(f'Successfully parsed profile for rider {self.id}')

  def __getattr__(self, name: str) -> Any:  # noqa: ANN401
    """Allow attribute access to any profile field.

    Provides fallback for fields not explicitly defined as attributes.

    Args:
        name: Field name

    Returns:
        Field value

    Raises:
        AttributeError: If field doesn't exist
    """
    if name.startswith('_'):
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      )
    try:
      return self._fetched[name]
    except KeyError:
      raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{name}'",
      ) from None

  def __getitem__(self, key: str) -> Any:  # noqa: ANN401
    """Allow dictionary-style access.

    Args:
        key: Field name

    Returns:
        Field value
    """
    return self._fetched[key]

  def __str__(self) -> str:
    """Return human-readable string with all profile data.

    Returns:
        Formatted string showing all profile fields
    """
    if not self._fetched:
      return 'ZwiftProfile(no data)'

    # Format all fields for display
    lines = ['ZwiftProfile(']
    for key, value in self._fetched.items():
      lines.append(f'  {key}: {value!r},')
    lines.append(')')
    return '\n'.join(lines)

  def __repr__(self) -> str:
    """Return detailed representation showing all fields.

    Returns:
        String representation with all profile data
    """
    if not self._fetched:
      return 'ZwiftProfile()'
    items = ', '.join(f'{k}={v!r}' for k, v in self._fetched.items())
    return f'ZwiftProfile({items})'

  def asdict(self) -> dict[str, Any]:
    """Return underlying data as dictionary.

    Returns:
        Profile data dictionary
    """
    return self._fetched

  def raw(self) -> str:
    """Return raw JSON response string.

    Returns:
        Raw JSON string from response.text
    """
    return self._raw

  def fetched(self) -> dict[str, Any]:
    """Return parsed data dictionary.

    Returns:
        Parsed dictionary from the raw JSON response
    """
    return self._fetched

  def json(self) -> str:
    """Serialize profile data to formatted JSON string.

    Returns:
        JSON string with 2-space indentation
    """
    return json.JSONEncoder(indent=2).encode(self._fetched)
