"""Conftest for zdatafetch module tests."""

import json

import pytest

from zdatafetch import ZwiftAuth, ZwiftProfile
from zdatafetch.followers import ZwiftFollowers
from zdatafetch.rideons import ZwiftRideOns


@pytest.fixture
def mock_credentials():
  """Mock Zwift credentials for testing."""
  return {'username': 'test@example.com', 'password': 'testpassword'}


@pytest.fixture
def mock_auth(mock_credentials):
  """Fixture for ZwiftAuth instance."""
  return ZwiftAuth(
    username=mock_credentials['username'],
    password=mock_credentials['password'],
  )


@pytest.fixture
def mock_profile(mock_auth):
  """Fixture for ZwiftProfile instance."""
  return ZwiftProfile(mock_auth)


@pytest.fixture
def mock_followers(mock_auth):
  """Fixture for ZwiftFollowers instance."""
  return ZwiftFollowers(mock_auth)


@pytest.fixture
def mock_rideons(mock_auth):
  """Fixture for ZwiftRideOns instance."""
  return ZwiftRideOns(mock_auth)


@pytest.fixture
def mock_token_response():
  """Mock OAuth2 token response."""
  return {
    'access_token': 'mock_access_token_12345',
    'token_type': 'Bearer',
    'expires_in': 3600,
    'refresh_token': 'mock_refresh_token_67890',
    'refresh_expires_in': 7200,
  }


@pytest.fixture
def mock_profile_data():
  """Mock profile data response."""
  return {
    'id': 550564,
    'publicId': 'abc123',
    'firstName': 'Test',
    'lastName': 'Rider',
    'male': True,
    'imageSrc': 'https://static-cdn.zwift.com/prod/profile/test-123',
    'imageSrcLarge': 'https://static-cdn.zwift.com/prod/profile/test-123-large',
    'countryAlpha3': 'USA',
    'countryCode': 226,
    'useMetric': True,
    'riding': False,
    'privacy': {
      'displayWeight': True,
      'minor': False,
      'privateMessaging': True,
      'defaultFitnessDataPrivacy': False,
      'suppressFollowerNotification': False,
      'displayAge': True,
      'defaultActivityPrivacy': 'PUBLIC',
    },
    'socialFacts': {
      'profileId': 550564,
      'followerCount': 123,
      'followeeCount': 456,
      'followeeStatusOfLoggedInPlayer': 'NO_RELATIONSHIP',
      'followerStatusOfLoggedInPlayer': 'NO_RELATIONSHIP',
    },
    'worldId': None,
    'enrolledZwiftAcademy': False,
    'playerType': 'NORMAL',
    'playerTypeId': 1,
    'connectedToStrava': True,
    'connectedToTrainingPeaks': False,
    'connectedToTodaysPlan': False,
    'connectedToUnderArmour': False,
    'connectedToWithings': False,
    'connectedToFitbit': False,
    'connectedToGarmin': False,
    'connectedToRuntastic': False,
    'connectedToZwiftCompanion': True,
    'avantlinkId': None,
    'connectedToFacebookMessenger': False,
    'profilePropertyChanges': None,
    'stravaPremium': False,
    'bt': None,
    'dob': '1975-01-15',
    'emailAddress': None,
    'height': 182,
    'location': None,
    'preferredLanguage': 'en-US',
    'mixpanelDistinctId': None,
    'profileChanges': False,
    'weight': 98000,
    'b': False,
    'createdOn': '2020-01-01T00:00:00.000+0000',
    'source': 'zwift',
    'origin': None,
    'launchedGameClient': '2020-01-01T12:00:00.000+0000',
    'ftp': 278,
    'userAgent': None,
    'runTime1miInSeconds': None,
    'runTime5kmInSeconds': None,
    'runTime10kmInSeconds': None,
    'runTimeHalfMarathonInSeconds': None,
    'runTimeFullMarathonInSeconds': None,
    'cyclingOrganization': None,
    'licenseNumber': None,
    'bigCommerceId': None,
    'marketingConsent': None,
    'publicAttributes': {
      'textField': None,
      'textFieldVisibility': 'PUBLIC',
    },
    'likelyInGame': False,
    'address': None,
    'achievementLevel': 25,
    'totalDistance': 12345678,
    'totalDistanceClimbed': 123456,
    'totalTimeInMinutes': 987654,
    'totalInKomJersey': 0,
    'totalInSprintersJersey': 0,
    'totalInOrangeJersey': 0,
    'totalWattHours': 5432100,
    'totalExperiencePoints': 987654,
    'totalGold': 12345,
    'runAchievementLevel': 5,
    'totalRunDistance': 234567,
    'totalRunTimeInMinutes': 12345,
    'totalRunExperiencePoints': 54321,
    'totalRunCalories': 45678,
    'powerSourceType': 'POWER_METER',
    'powerSourceModel': 'Stages',
    'virtualBikeModel': None,
    'numberOfFolloweesInCommon': 0,
  }


@pytest.fixture
def mock_profile_not_found():
  """Mock 404 response for profile not found."""
  return {'message': 'Profile not found', 'statusCode': 404}


@pytest.fixture
def auth_handler(mock_token_response):
  """HTTP handler for authentication requests."""
  import httpx2

  def handler(request):
    if 'auth/realms/zwift/tokens/access/codes' in str(request.url):
      if request.method == 'POST':
        # Check the grant_type to determine if it's login or refresh
        body = request.content.decode('utf-8')
        if 'grant_type=password' in body:
          # Initial login
          return httpx2.Response(200, text=json.dumps(mock_token_response))
        if 'grant_type=refresh_token' in body:
          # Token refresh
          return httpx2.Response(200, text=json.dumps(mock_token_response))
        return httpx2.Response(400, text='Invalid grant_type')
    return httpx2.Response(404)

  return handler


@pytest.fixture
def profile_handler(mock_profile_data):
  """HTTP handler for profile requests."""
  import httpx2

  def handler(request):
    if '/api/profiles/' in str(request.url):
      # Check for authorization header
      if 'Authorization' not in request.headers:
        return httpx2.Response(401, text='Unauthorized')

      # Extract rider ID from URL
      url_parts = str(request.url).split('/')
      rider_id = url_parts[-1]

      if rider_id == '550564':
        return httpx2.Response(200, text=json.dumps(mock_profile_data))
      if rider_id == '999999':
        return httpx2.Response(404, text='Profile not found')
      return httpx2.Response(200, text=json.dumps(mock_profile_data))

    return httpx2.Response(404)

  return handler


@pytest.fixture
def combined_handler(auth_handler, profile_handler):
  """Combined HTTP handler for auth and profile requests."""
  import httpx2

  def handler(request):
    # Try auth handler first
    if 'auth/realms/zwift/tokens/access/codes' in str(request.url):
      return auth_handler(request)
    # Then try profile handler
    if '/api/profiles/' in str(request.url):
      return profile_handler(request)
    return httpx2.Response(404)

  return handler
