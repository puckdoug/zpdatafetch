"""Zwift unofficial API data fetching library.

This package provides programmatic access to Zwift's unofficial API endpoints
for fetching rider profiles, activity data, and social information.

Usage:
    from zdatafetch import ZwiftAuth, ZwiftProfile

    # Authenticate
    auth = ZwiftAuth(username, password)
    auth.login()

    # Fetch profile
    profile = ZwiftProfile(auth)
    profile.fetch(550564)
    print(profile.json())

Classes:
    ZwiftAuth: Handles Zwift API authentication
    ZwiftProfile: Fetches and stores rider profile data
    ZwiftFollowers: Fetches follower data (not yet implemented)
    ZwiftRideOns: Fetches RideOn data (not yet implemented)
"""

from zdatafetch.auth import ZwiftAuth
from zdatafetch.config import Config
from zdatafetch.profile import ZwiftProfile

__all__ = ['Config', 'ZwiftAuth', 'ZwiftProfile']
