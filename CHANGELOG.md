# Changelog

## [Unreleased]

### Added

- pytest-cov for automated coverage reporting
- Code review documentation (REVIEW.md, IMPROVEMENTS.md)

### Changed

- Removed all unused imports for cleaner codebase
- Updated pyproject.toml with pytest-cov configuration

### Fixed

- Resolved 21 ruff linting warnings (unused imports)

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
