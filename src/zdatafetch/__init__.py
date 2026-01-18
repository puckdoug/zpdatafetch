"""Zwift unofficial API data fetching library.

This package provides programmatic access to Zwift's unofficial API endpoints
for fetching rider profiles, activity data, and social information.

Usage:
    from zdatafetch import ZwiftProfile, ZwiftFollowers, ZwiftRideOns

    # Fetch profile
    profile = ZwiftProfile()
    profile.fetch(550564)
    print(profile.json())

    # Fetch followers
    followers = ZwiftFollowers()
    followers.fetch(550564)
    print(f"Followers: {followers.follower_count()}")

    # Fetch RideOns
    rideons = ZwiftRideOns()
    rideons.fetch(550564, 12345678)
    print(f"RideOns: {rideons.rideon_count()}")

    # Give RideOn
    ZwiftRideOns.give_rideon(550564, 12345678)

Classes:
    ZwiftAuth: Handles Zwift API authentication
    ZwiftProfile: Fetches and stores rider profile data
    ZwiftFollowers: Fetches follower and followee data
    ZwiftRideOns: Fetches RideOn data and gives RideOns
"""

from zdatafetch.activity import ZwiftActivity
from zdatafetch.auth import ZwiftAuth
from zdatafetch.config import Config
from zdatafetch.followers import ZwiftFollowers
from zdatafetch.profile import ZwiftProfile
from zdatafetch.rideons import ZwiftRideOns
from zdatafetch.ridersinworld import ZwiftRidersInWorld
from zdatafetch.worlds import ZwiftWorlds

__all__ = [
  'Config',
  'ZwiftActivity',
  'ZwiftAuth',
  'ZwiftFollowers',
  'ZwiftProfile',
  'ZwiftRideOns',
  'ZwiftRidersInWorld',
  'ZwiftWorlds',
]
