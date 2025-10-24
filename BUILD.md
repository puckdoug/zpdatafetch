# Build and Release Guide

This document describes how to build and release zpdatafetch to PyPI.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Build](#local-development-build)
- [Running Tests](#running-tests)
- [Creating a Release](#creating-a-release)
- [Automated Release Process](#automated-release-process)
- [Manual Release Process](#manual-release-process)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Python**: 3.10 or higher (supports 3.10-3.14 including 3.14t, excluding 3.13t)
- **uv**: [Astral's uv package manager](https://astral.sh/uv) (recommended) or pip
- **build**: Python build frontend (`python -m build`)
- **Git**: For version control and tagging

### Installation

```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip
pip install uv
```

### PyPI Credentials

For manual releases, you'll need:
- PyPI account with access to the zpdatafetch project
- PyPI API token stored in `~/.pypirc` or available via environment variable

For automated releases (GitHub Actions):
- `PYPI_API_TOKEN` secret configured in GitHub repository settings

## Local Development Build

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/zpdatafetch.git
cd zpdatafetch

# Sync dependencies
uv sync --all-extras --dev

# Build the package
uv run python -m build
```

This creates both:
- Source distribution: `dist/zpdatafetch-<version>.tar.gz`
- Wheel distribution: `dist/zpdatafetch-<version>-py3-none-any.whl`

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Build the package
python -m build
```

## Running Tests

Tests must pass before creating a release.

### Run All Tests

```bash
# Using uv
uv run pytest

# Using pip
pytest
```

### Run Tests with Coverage

```bash
uv run pytest --cov=zpdatafetch --cov-report=html
```

### Run Specific Test Categories

```bash
# Just logging tests
uv run pytest test/test_logging.py

# Just core functionality tests
uv run pytest test/test_zp.py

# Verbose output
uv run pytest -xvs
```

### Platform-Specific Testing

The CI/CD pipeline tests on:
- **Linux**: Ubuntu (Python 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t)
- **Windows**: Latest (Python 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t)

## Creating a Release

### Version Management

1. Update version in `pyproject.toml`:
   ```toml
   [project]
   name = "zpdatafetch"
   version = "1.2.0"  # Update this
   ```

2. Update `CHANGELOG.md` (if present) with release notes

3. Commit the version change:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 1.2.0"
   git push origin main
   ```

### Tag Format

Releases are triggered by tags matching the pattern: `release_*`

**Recommended format**: `release_<short-commit-hash>`

```bash
# Get the current commit hash
git rev-parse --short HEAD
# Example output: a1b2c3d

# Create and push release tag
git tag release_a1b2c3d
git push origin release_a1b2c3d
```

**Alternative format**: `release_v<version>`

```bash
git tag release_v1.2.0
git push origin release_v1.2.0
```

## Automated Release Process

The automated release uses GitHub Actions and runs when you push a tag starting with `release_`.

### Workflow Sequence

1. **Tag Push** → Triggers test and build workflows
   ```bash
   git tag release_$(git rev-parse --short HEAD)
   git push origin release_$(git rev-parse --short HEAD)
   ```

2. **Tests Run in Parallel**
   - `linux-test`: Tests on Ubuntu with Python 3.10-3.14
   - `windows-test`: Tests on Windows with Python 3.10-3.14

3. **Build and Release** (only if tests pass)
   - Waits for both test workflows to complete successfully
   - Builds source distribution and wheel
   - Publishes to PyPI using `PYPI_API_TOKEN`

### Requirements for Automated Release

#### GitHub Repository Settings

1. **Environment**: Create a `release` environment
   - Go to Settings → Environments → New environment
   - Name: `release`

2. **Secrets**: Add PyPI API token
   - Go to Settings → Secrets and variables → Actions
   - New repository secret: `PYPI_API_TOKEN`
   - Value: Your PyPI API token

#### PyPI API Token Setup

1. Log in to [PyPI](https://pypi.org/)
2. Go to Account Settings → API tokens
3. Create a new token:
   - Name: `zpdatafetch-github-actions`
   - Scope: Project (select `zpdatafetch`)
4. Copy the token (starts with `pypi-`)
5. Add to GitHub secrets as `PYPI_API_TOKEN`

### Monitoring the Release

1. Go to GitHub Actions tab
2. Watch for three workflows:
   - `linux-test` - Should complete successfully
   - `windows-test` - Should complete successfully
   - `build and release` - Should trigger after tests pass

3. Check workflow logs if release fails:
   ```
   Actions → build and release → Latest run → View logs
   ```

4. Verify on PyPI:
   - Check [https://pypi.org/project/zpdatafetch/](https://pypi.org/project/zpdatafetch/)
   - New version should appear within 5-10 minutes

## Manual Release Process

If automated release fails or you need to release manually:

### Build Locally

```bash
# Ensure clean state
git clean -fdx
git checkout main
git pull

# Sync dependencies
uv sync --all-extras --dev

# Run tests
uv run pytest

# Build distributions
uv run python -m build
```

### Upload to TestPyPI (Optional - for testing)

```bash
# Install twine
uv pip install twine

# Upload to TestPyPI
uv run twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ zpdatafetch
```

### Upload to PyPI

```bash
# Upload to PyPI
uv run twine upload dist/*

# Enter your PyPI credentials when prompted
# Or use API token: username = __token__, password = pypi-...
```

## Troubleshooting

### Tests Fail on CI but Pass Locally

- Check Python version compatibility
- Review test logs in GitHub Actions
- Common issues:
  - Platform-specific path issues (Windows vs Linux)
  - Environment variables not set
  - Missing test fixtures

### Build Workflow Doesn't Trigger

Check:
1. Tag format matches `release_*` pattern
2. Tests workflows are configured to run on tags
3. Both test workflows completed successfully
4. GitHub Actions are enabled for the repository

Debug with:
```bash
# View recent workflow runs
gh run list --workflow="build and release"

# View specific run details
gh run view <run-id>
```

### Release Published but Not Appearing on PyPI

- Check PyPI status: [https://status.python.org/](https://status.python.org/)
- Verify API token has correct permissions
- Check workflow logs for upload errors
- Wait 5-10 minutes for PyPI to index the package

### Version Conflicts

If PyPI rejects with "File already exists":
- You cannot re-upload the same version
- Increment version in `pyproject.toml`
- Create a new tag and push again

### Keyring Issues During Build

The package requires keyring for credential management. If build fails:

```bash
# Set up test credentials
export ZWIFTPOWER_USERNAME="test"
export ZWIFTPOWER_PASSWORD="test"

# Or use PlaintextKeyring for testing
export PYTHON_KEYRING_BACKEND=keyring.backends.PlaintextKeyring
```

## Best Practices

### Before Each Release

1. ✅ Run full test suite locally
2. ✅ Update version in `pyproject.toml`
3. ✅ Update documentation if API changed
4. ✅ Test build process locally
5. ✅ Commit all changes to main
6. ✅ Tag with descriptive release tag
7. ✅ Monitor CI/CD pipeline
8. ✅ Verify PyPI upload succeeded
9. ✅ Test installation from PyPI: `pip install --upgrade zpdatafetch`

### Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):
- **Major** (1.0.0 → 2.0.0): Breaking API changes
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Patch** (1.0.0 → 1.0.1): Bug fixes, backward compatible

### Release Checklist

- [ ] All tests pass locally
- [ ] Version bumped in `pyproject.toml`
- [ ] Changes documented in CHANGELOG (if present)
- [ ] README updated (if needed)
- [ ] Committed and pushed to main
- [ ] Tagged with `release_*` format
- [ ] CI/CD pipeline succeeded
- [ ] Package appears on PyPI
- [ ] Installation from PyPI works
- [ ] GitHub release created (optional)

## GitHub Release Notes (Optional)

After successful PyPI upload, create a GitHub release:

```bash
# Using GitHub CLI
gh release create release_a1b2c3d \
  --title "v1.2.0" \
  --notes "Release notes here" \
  dist/*

# Or manually via GitHub web interface
# Go to Releases → Draft a new release
```

## Support

For issues with the build or release process:
- Check [GitHub Actions logs](https://github.com/yourusername/zpdatafetch/actions)
- Review [GitHub Issues](https://github.com/yourusername/zpdatafetch/issues)
- Consult [PyPI documentation](https://packaging.python.org/)
