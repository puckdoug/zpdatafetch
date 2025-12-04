# Changelog

## [1.7.1]

- Resolved issue preventing signups and teams from fetching correctly in 1.7.0.

## [1.7.0] - Yanked

### Changed

- **BREAKING: Raw data storage refactoring** - All data classes now store truly raw JSON strings in `_raw`/`raw` attributes instead of parsed dictionaries
  - **zpdatafetch package**: `raw` attribute now stores `dict[int, str]` (mapping IDs to JSON strings) instead of `dict[int, dict]`
    - Added new `processed` attribute storing `dict[int, dict[str, Any]]` with parsed data
    - Affects: `Cyclist`, `Result`, `Team`, `Primes`, `Sprints`, `Signup` classes
    - `Primes` and `Sprints` maintain their nested structure in both `raw` and `processed` attributes
  - **zrdatafetch package**: `_raw` attribute now stores raw JSON strings instead of parsed dictionaries
    - Affects: `ZRRider`, `ZRResult`, `ZRTeam` classes
    - Parsing happens explicitly via `_parse_response()` method
  - All `fetch_json()` methods now return `str` instead of `dict[str, Any]`
  - JSON parsing centralized using `parse_json_safe()` helper with context-aware error messages
- Reorganized codebase structure with shared utilities in `./shared` module
  - Created `shared.json_helpers` module for centralized JSON parsing
  - Created `shared.validation` module for input validation
  - Created `shared.exceptions` module for exception hierarchy
  - Created `shared.config` module for base configuration classes
  - Created `shared.http_client` module for HTTP client utilities
  - Created `shared.error_helpers` module for error formatting
  - Created `shared.logging` module for logging configuration
  - Created `shared.cli` module for CLI utilities
- Improved error messages with more context and actionable suggestions
- Enhanced type handling and input validation across all modules
- Reorganized test structure for better maintainability
- Updated Zwiftracing.app API endpoints to use new server

### Added

- New `shared` package containing reusable utilities for both zpdatafetch and zrdatafetch
- `parse_json_safe()` helper function with context-aware error messages
- Context information in all JSON parsing operations for better debugging
- Comprehensive test coverage for raw data storage refactoring

### Fixed

- Fixed test isolation issues - `test_batch_accepts_invalid_ids_currently` now properly mocks both Config and fetch_json to avoid real API calls
- Removed unused imports: `json` from multiple ZP and ZR modules, `Any` from json_helpers, `ValidationError` and `validate_id_list` from sprints
- Fixed ZRResult to handle format delivered by new ZwiftRacing endpoint with updated fixture for future testing
- Fixed inconsistent data storage - raw data is now truly raw across all classes
- Fixed Sprints `extract_banners()` method to use `processed` attribute instead of `raw`
- Fixed Sprints `enrich_sprints()` method to properly handle data enrichment

### Developer Notes

- Code quality improvements: Fixed multiple linting issues and removed code duplication
- All changes maintain backward compatibility for end users through the unified `fetch()`/`afetch()` API

## [1.6.2] - Yanked

### Changed

- Updated underlying fetch used by the system to use async processes. This allows parallelizing fetches when more than one object is fetched or when more than one call is requried as with primes and sprints. Results in a slight speed-up.

## [1.6.1] - Yanked

### Changed

- Updated sprint logic to pull in banner names from Primes
- Updated all objects to allow session sharing (zp_obj, zr_obj) so that only one login is required per session
- Updated README to describe how this works.

## [1.6.0]

### Added

- New `Sprints` endpoint for fetching sprint data from ZwiftPower
  - Fetches data from `api3.php?do=event_sprints&zid=<race_id>`
  - Supports both synchronous `fetch()` and asynchronous `afetch()` methods
  - Returns sprint data organized by race ID
  - Full test coverage with sync and async tests
- `sprints` command to zpdata CLI tool

### Changed

- **BREAKING: `Primes.fetch()` return value** - Now returns a dictionary of nested structure `{race_id: {category: {prime_type: data}}}` instead of a flat structure
- **BREAKING: `Primes.afetch()` return value** - Now returns the same nested dictionary structure as `fetch()` for consistency
- `Primes.afetch()` now uses the same `api3.php` endpoint as `fetch()` instead of the non-functional `cache3/primes` endpoint
- Updated README.md to document the new Sprints endpoint and updated CLI usage examples

### Fixed

- Fixed `Primes.afetch()` to use working `api3.php` endpoint instead of non-functional `cache3/primes` endpoint
- Fixed inconsistency between `Primes.fetch()` and `Primes.afetch()` - both now call identical endpoints and return identical data structures
- Fixed `test_async_primes.py` to validate the new nested dictionary structure returned by `afetch()`

## [1.5.0]

### Added

- Reorganized async API to be integrated with regular data classes for simplified interface
  - All data classes (`Cyclist`, `Result`, `Signup`, `Team`, `Primes`, `ZRRider`, `ZRResult`, `ZRTeam`) now support both sync and async methods
  - Removed separate `AsyncCyclist`, `AsyncResult`, etc. classes (now aliases for backwards compatibility)
  - Unified `fetch()` and `afetch()` methods on all classes
- Improved test organization with individual async test files per endpoint

### Changed

- **BREAKING: Unified API design** - Removed separate async classes; `fetch()` and `afetch()` are now methods on the same class
  - `type(obj)` returns the same class regardless of sync/async usage
  - Simplified imports: no need for separate `Async*` classes
- Reorganized async tests into individual files (`test_async_cyclist.py`, `test_async_primes.py`, etc.) instead of single `test_async_data_classes.py`
- Updated GitHub workflow - removed conditional checks on manual build to allow manual triggering at any time
- Updated README.md with unified async API documentation and examples

### Fixed

- Simplified async API interface by consolidating async functionality into base classes
- Improved test organization and maintainability

## [1.4.0]

### Added

- Full Python 3.14 support with compatibility fixes for httpcore library
- ZwiftRacing API support via new `zrdatafetch` module
  - `AsyncZR_obj` base class for async ZwiftRacing API operations
  - `ZRRider` class for fetching rider profiles and rankings
  - `ZRResult` class for fetching race results
  - `ZRTeam` class for fetching team/club information
  - Rate limiting support for ZwiftRacing API endpoints
  - Async versions of all ZwiftRacing classes with trio/asyncio support
- `zrdata` command-line tool for ZwiftRacing API access
- Rate limiter module with configurable limits per endpoint type
- Comprehensive test coverage for all new ZwiftRacing functionality

### Changed

- Improved test isolation - all tests now use mocked network connections
- Updated httpcore compatibility for Python 3.14 (patched type alias attribute setting)

### Fixed

- Fixed tests making real network connections to live websites
  - `test/test_zr_obj.py`: Now properly mocks all `httpx.Client()` instantiation
  - `test/test_async_zr.py`: Completely rewrote tests to use `AsyncMock` and `patch`
  - `test/test_async_zrrider.py`: Added proper mocking for shared session tests
- Fixed Python 3.14 compatibility issue where httpcore 1.0.5 attempted to set `__module__` attribute on immutable `typing.Union` objects
- Fixed 37 test failures on Python 3.14 related to httpcore/typing incompatibility
- Resolved 3 xfail tests that now pass on Python 3.14 (httpcore shared client tests)

## [1.2.0]

### Security

- Fixed credential exposure in debug logging - Removed credential URL logging from authentication process to prevent accidental exposure in debug logs or centralized logging systems
- Removed insecure Config.dump() method - Eliminated dangerous method that printed plaintext passwords to stdout; replaced with safe `verify_credentials_exist()` method
- Added input validation - All data fetcher classes (`Cyclist`, `Primes`, `Result`, `Signup`, `Team`) now validate ID parameters to prevent injection attacks and DoS attempts
- Implemented automatic credential cleanup - Added `clear_credentials()` method that securely clears credentials from memory; automatically called on object cleanup and context manager exit
- Made HTTPS certificate verification explicit - Changed from implicit to explicit `verify=True` in HTTP client initialization to prevent MITM attacks and ensure security is intentional and auditable
- Credentials are now overwritten in memory before deletion to reduce recovery risk from memory dumps

### Added

- pytest-cov for automated coverage reporting
- Code review documentation (REVIEW.md, IMPROVEMENTS.md)
- Context manager support: All library classes now support the `with` statement for automatic resource cleanup
- Connection pooling: New `shared_client` parameter enables HTTP connection reuse across multiple instances for improved batch performance
- Automatic retry logic: Built-in exponential backoff retry mechanism for transient network failures (connection errors, timeouts, 5xx errors)
- GitHub Actions CI: Migrated to official `astral-sh/setup-uv` action with uv 0.9.5 and modern `[dependency-groups]` syntax
- Credential cleanup: `clear_credentials()` method in `Config` and `ZP` classes for secure memory management
- Safe credential verification: `Config.verify_credentials_exist()` method as secure alternative to removed `dump()` method
- Input validation: All data fetcher classes now validate ID parameters (positive integers within bounds)

### Changed

- Removed all unused imports for cleaner codebase
- Updated pyproject.toml with pytest-cov configuration and modern `[dependency-groups]` syntax
- `ZP` class now supports context management via `__enter__()` and `__exit__()` methods
- `fetch_json()` and `fetch_page()` methods now include automatic retry with exponential backoff (configurable via `max_retries` and `backoff_factor` parameters)
- Enhanced HTTP client initialization to support connection pooling with new `init_client()` method
- Updated GitHub Actions workflows to use official Astral setup-uv action with built-in caching
- Input validation in all data fetchers now accepts both integer and string inputs (for CLI compatibility)
- Credentials are automatically cleared from memory when using context managers or calling `close()`

### Fixed

- Resolved 21 ruff linting warnings (unused imports)
- Fixed 24 ruff errors in test suite (star imports, string comparisons, unused imports)
- Fixed critical bug where CLI would reject valid numeric string IDs (now accepts both int and string inputs)
- Fixed credential memory retention issue - credentials now cleared on object destruction
- Fixed implicit HTTPS verification - now explicit in configuration

### Removed

- **BREAKING: Removed `Config.dump()` method** - This insecure method printed plaintext passwords to stdout. Use `verify_credentials_exist()` instead to check if credentials are configured.

### Known Issues

- **test_shared_client_connection_pooling on Python 3.14**: Test is marked as xfail (expected failure) due to httpcore 1.1.x bug with Python 3.14 typing.Union. This is an upstream issue in encode/httpcore that will be fixed in version 1.2.0+. The test demonstrates the feature works on Python 3.10-3.13.

### Security Advisory

This release includes critical security fixes addressing credential exposure vulnerabilities. Users are strongly encouraged to upgrade. The following changes may affect existing code:

- `Config.dump()` method has been removed (security risk)
- Credentials are now cleared from memory automatically
- All ID parameters are validated before use

## [1.1.3] - 2024-10-26

### Added

- Support for Python 3.14 and 3.14t (free-threaded)
- Comprehensive logging system with setup_logging() function
- File and console logging support with different verbosity levels
- Flexible logging configuration for library and CLI usage

### Changed

- Updated lxml from >=5.2.1 to >=5.4.0 for Python 3.14 wheel support
- Updated httpx from >=0.27.0 to >=0.28.0 for Python 3.14 compatibility
- Added explicit cryptography>=44.0.0 constraint for Python 3.14t support
- Updated dependencies to resolve Python 3.14 compatibility issues

### Fixed

- Fixed Windows file locking issues in logging tests
- Fixed lxml 5.3.0 build failures on Python 3.14
- Fixed httpcore compatibility issues with Python 3.14
- Fixed cryptography build issues on Python 3.14t free-threaded

### Deprecated

- tool.uv.dev-dependencies configuration (plan to migrate to dependency-groups)

## [1.1.2] - 2024-XX-XX

### Added

- Initial Python 3.13 support (excluding 3.13t)

### Fixed

- Various dependency version incompatibilities
- Test compatibility improvements

## [1.1.1] - 2024-XX-XX

### Fixed

- Bug fixes and stability improvements

## [1.1.0] - 2024-XX-XX

### Added

- Initial public release
- Command-line interface (zpdata)
- Library interface for programmatic access
- Support for fetching athlete profiles, race results, signups, team rosters, and primes
- System keyring integration for secure credential management
- Support for Python 3.10, 3.11, 3.12, 3.13

### Features

- Fetch cyclist profile data by Zwift ID
- Fetch team roster data by team ID
- Fetch race results by event ID
- Fetch race signups by event ID
- Fetch prime/segment data by event ID
- Flexible logging with console and file output
- JSON and dictionary output formats
