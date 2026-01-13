# zdatafetch - Zwift Unofficial API Library

A Python library and CLI tool for fetching data from Zwift's unofficial API.

## Overview

`zdatafetch` provides access to Zwift's reverse-engineered mobile API endpoints for retrieving rider profiles, activity data, and social information. It uses OAuth2 authentication with regular Zwift account credentials.

**Note:** This uses Zwift's unofficial/undocumented API. While Zwift officially states they don't provide a public API, the mobile app uses these endpoints which have been reverse-engineered by the community.

## Installation

```bash
# From the zpdatafetch repository root
uv pip install -e .
```

## Quick Start

### CLI Usage

```bash
# Configure credentials (stored securely in system keyring)
zdata config

# Fetch a rider profile
zdata profile 550564

# Fetch multiple profiles
zdata profile 550564 789012 345678

# Get raw JSON output
zdata profile --raw 550564

# Check what would be fetched without actually fetching
zdata profile --noaction 550564
```

### Library Usage

```python
from zdatafetch import ZwiftAuth, ZwiftProfile

# Authenticate
auth = ZwiftAuth(username='your@email.com', password='yourpassword')
auth.login()

# Fetch profile
profile = ZwiftProfile(auth)
profile.fetch(550564)

# Access data
print(profile.json())  # Formatted JSON string
print(profile.asdict())  # Python dictionary
print(profile.get(550564))  # Specific rider's data
```

## Features

### Currently Implemented

- **Profile Fetching** (`profile` command)
  - Complete rider profile data
  - Demographics (name, age, gender, country)
  - Physical stats (height, weight)
  - Activity statistics (distance, climbing, XP, gold)
  - Social data (followers, following)
  - Connected services (Strava, Garmin, etc.)

### Planned (Not Yet Implemented)

- **Followers** (`followers` command) - Fetch follower/followee lists
- **RideOns** (`rideons` command) - Fetch and give RideOns

## API Endpoints

Based on [unofficial Zwift API documentation](https://github.com/strukturunion-mmw/zwift-api-documentation):

- **Authentication:** `POST https://secure.zwift.com/auth/realms/zwift/tokens/access/codes`
- **Profile:** `GET https://us-or-rly101.zwift.com/api/profiles/{riderId}`

## Configuration

Credentials are stored securely using your system's keyring:
- **macOS:** Keychain
- **Windows:** Windows Credential Manager
- **Linux:** Secret Service API / KWallet / GNOME Keyring

```bash
# Set up credentials
zdata config

# Credentials are stored under service name: zdatafetch
```

## Command Reference

### zdata profile

Fetch rider profile data from Zwift's API.

```bash
zdata profile <rider_id> [<rider_id> ...]

Options:
  --raw         Output raw JSON as received from API
  --noaction    Show what would be fetched without fetching
  -v            Verbose output (INFO level logging)
  -vv           Debug output (DEBUG level logging)
```

**Example Output (formatted):**
```json
{
  "550564": {
    "id": 550564,
    "firstName": "Doug",
    "lastName": "Morris",
    "male": true,
    "age": 50,
    "countryAlpha3": "CHE",
    "height": 182,
    "weight": 98000,
    "totalDistance": 12345678,
    "socialFacts": {
      "followerCount": 123,
      "followeeCount": 456
    },
    "connectedToStrava": true
  }
}
```

### zdata followers

**Status:** Not yet implemented

Will fetch follower/followee lists for riders.

```bash
zdata followers <rider_id>
# Currently returns: "Follower fetching is not yet implemented. Coming soon!"
```

### zdata rideons

**Status:** Not yet implemented

Will fetch RideOn data for activities.

```bash
zdata rideons <activity_id>
# Currently returns: "RideOn fetching is not yet implemented. Coming soon!"
```

## Architecture

```
zdatafetch/
├── __init__.py       # Package exports
├── auth.py           # OAuth2 authentication
├── config.py         # Credential management
├── profile.py        # Profile data fetching
├── followers.py      # Followers (stub)
├── rideons.py        # RideOns (stub)
├── cli.py            # Command-line interface
└── logging_config.py # Logging setup
```

## Error Handling

The library raises specific exceptions for different error conditions:

- `AuthenticationError` - Invalid credentials or authentication failure
- `NetworkError` - Network connectivity issues or API request failures
- `ConfigError` - Missing or invalid configuration
- `NotImplementedError` - Feature not yet implemented

## Development

```bash
# Run linting
ruff check src/zdatafetch

# Test CLI
zdata --help
zdata profile --noaction 550564
```

## Comparison with zpdatafetch

| Feature | zpdatafetch | zdatafetch |
|---------|-------------|------------|
| Data Source | ZwiftPower.com | Zwift API |
| Authentication | ZwiftPower login | Zwift login |
| Race Results | ✅ | ❌ |
| Race Signups | ✅ | ❌ |
| Team Data | ✅ | ❌ |
| Rider Profile | ✅ (limited) | ✅ (complete) |
| Live Activity | ❌ | 🔜 (planned) |
| Social Data | ❌ | 🔜 (planned) |
| Racing Score | ❌ | 🔜 (via profile) |

## References

- [Zwift API Unofficial Documentation](https://github.com/strukturunion-mmw/zwift-api-documentation)
- [zwift-client Python Library](https://github.com/jsmits/zwift-client)
- [Zwift Insider: Racing Score API Access](https://zwiftinsider.com/zwiftpower-zrs/)

## License

MIT License - Same as parent zpdatafetch package

## Disclaimer

This library uses Zwift's unofficial API which is not publicly documented or officially supported. Zwift has stated they do not provide a public API for hobby developers. Use at your own risk. The API endpoints may change without notice.
