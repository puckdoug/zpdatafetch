# Contributing to zpdatafetch

Guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic familiarity with command line

### Development Setup

1. **Fork and clone the repository:**

```bash
git clone https://github.com/puckdoug/zpdatafetch.git
cd zpdatafetch
```

2. **Install development dependencies:**

```bash
# Using uv (recommended)
uv sync --all-extras --dev

# Or using pip
pip install -e ".[dev]"
```

3. **Set up test credentials:**

```bash
keyring set zpdatafetch username your_zwiftpower_username
keyring set zpdatafetch password your_zwiftpower_password
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest test/test_zp.py

# Run with verbose output
uv run pytest -xvs

# Run a specific test
uv run pytest test/test_zp.py::test_login_success

# Run tests with coverage report
uv run pytest --cov=zpdatafetch --cov-report=html
```

### Code Quality Checks

```bash
# Run linter
uv run ruff check src

# Fix linting issues automatically
uv run ruff check src --fix

# Format code
uv run ruff format src

# Run all checks before commit
uv run ruff check src && uv run pytest
```

## Code Style

### General Guidelines

- Maximum line length: 80 characters
- Use type hints for all function parameters and returns
- Write docstrings for all public functions and classes
- Use modern Python 3.10+ syntax
- Follow the existing code patterns in the project

### Type Hints

All functions must have complete type hints:

```python
# Good - modern Python 3.10+ style
def fetch(self, endpoint: str) -> dict[str, Any]:
    """Fetch data from endpoint.

    Args:
        endpoint: URL to fetch from

    Returns:
        Dictionary containing the response
    """
    pass

# Avoid - old typing style
from typing import Dict
def fetch(self, endpoint: str) -> Dict[str, Any]:
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def fetch_json(self, endpoint: str) -> dict[str, Any]:
    """Fetch JSON data from a Zwiftpower endpoint.

    Automatically logs in if not already authenticated.

    Args:
        endpoint: Full URL of the JSON endpoint to fetch

    Returns:
        Dictionary containing the parsed JSON response

    Raises:
        ZPNetworkError: If the HTTP request fails
        ZPAuthenticationError: If authentication fails
    """
```

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/description-of-feature
```

Branch naming conventions:

- `feature/`: New features
- `fix/`: Bug fixes
- `docs/`: Documentation updates
- `test/`: Test improvements
- `refactor/`: Code refactoring

### 2. Make Your Changes

- Keep commits atomic and focused
- Write clear commit messages
- Test your changes frequently

### 3. Commit Your Work

```bash
# Good commit messages describe what and why
git commit -m "Add retry logic for network errors

- Implements exponential backoff
- Retries on connection errors and timeouts
- Logs retry attempts for debugging"
```

### 4. Push to Your Fork

```bash
git push origin feature/description-of-feature
```

### 5. Create a Pull Request

On GitHub:

- Open a new Pull Request
- Reference any related issues: `Fixes #123`
- Provide a clear description of changes
- Ensure all checks pass

## Pull Request Guidelines

Your PR will be reviewed for:

### Code Quality

- ✅ No ruff warnings: `uv run ruff check src`
- ✅ Consistent code style
- ✅ Type hints on all functions
- ✅ No unused imports or variables

### Testing

- ✅ All tests pass: `uv run pytest`
- ✅ New features include tests
- ✅ Bug fixes include regression tests
- ✅ No test coverage reduction

### Documentation

- ✅ Docstrings for new functions/classes
- ✅ README updates if API changes
- ✅ CHANGELOG.md updated
- ✅ Comments for complex logic

## Testing Requirements

### For New Features

1. Add tests in `test/` directory following naming convention `test_*.py`
2. Test both success and failure cases
3. Update relevant documentation
4. Add entry to `CHANGELOG.md` under `[Unreleased]`

Example:

```python
def test_fetch_with_retry_success():
    """Test fetch succeeds after retry."""
    # Your test code
    pass

def test_fetch_network_error_retry():
    """Test fetch retries on network error."""
    # Your test code
    pass
```

### For Bug Fixes

1. Add a regression test that would fail with the old code
2. Make your fix
3. Verify the new test passes
4. Add entry to `CHANGELOG.md` under `[Unreleased] > Fixed`

## Project Structure

```
zpdatafetch/
├── src/zpdatafetch/          # Main source code
│   ├── __init__.py           # Package exports
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Credential management
│   ├── cyclist.py           # Cyclist data fetching
│   ├── logging_config.py    # Logging setup
│   ├── primes.py            # Primes data fetching
│   ├── result.py            # Results data fetching
│   ├── signup.py            # Signup data fetching
│   ├── team.py              # Team data fetching
│   ├── zp.py                # Core API client
│   └── zp_obj.py            # Base class for data objects
├── test/                     # Test suite
│   ├── conftest.py          # Pytest configuration
│   ├── fixtures/            # Test fixtures
│   └── test_*.py            # Test modules
├── pyproject.toml           # Project configuration
├── README.md                # User documentation
├── BUILD.md                 # Build and release guide
├── CONTRIBUTING.md          # This file
├── CHANGELOG.md             # Version history
└── REVIEW.md                # Architecture notes
```

## Common Tasks

### Adding a New Data Type

1. Create `src/zpdatafetch/newtype.py`
2. Inherit from `ZP_obj`
3. Implement `fetch()` method
4. Add tests in `test/test_newtype.py`
5. Update `__init__.py` exports
6. Update README with usage example

### Adding a CLI Command

1. Add case to match statement in `cli.py`
2. Create corresponding data class
3. Add help text to argument parser
4. Add tests for new command
5. Update README CLI section

### Updating Dependencies

1. Update version constraints in `pyproject.toml`
2. Run `uv sync --all-extras --dev`
3. Run tests to verify compatibility
4. Update `CHANGELOG.md`

### For Maintainers

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit changes: `git commit -m "Bump version to X.Y.Z"`
4. Create and push tag: `git tag release_vX.Y.Z && git push origin release_vX.Y.Z`
5. GitHub Actions will automatically test, build, and publish to PyPI

## Questions or Need Help?

- Check existing [issues](https://github.com/puckdoug/zpdatafetch/issues)
- Search [discussions](https://github.com/puckdoug/zpdatafetch/discussions)
- Create a new issue with your question
- Review `README.md` and `BUILD.md` for documentation

## Additional Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Keep a Changelog Format](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

## License

By contributing to zpdatafetch, you agree that your contributions will be licensed under the same license as the project (MIT License).
