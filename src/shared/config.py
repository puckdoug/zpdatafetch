"""Abstract base class for credential management using system keyring.

Provides common functionality for storing and retrieving credentials from the
system keyring service. Subclasses must implement credential-specific logic
for different credential types (username/password vs. authorization token, etc).
"""

from abc import ABC, abstractmethod
from typing import Any

import keyring
from keyring.backend import KeyringBackend

from shared.logging import get_logger

logger = get_logger(__name__)


# ==============================================================================
class BaseConfig(ABC):
  """Abstract base class for managing credentials using system keyring.

  Provides common keyring-based credential storage functionality that can be
  customized by subclasses for different credential types.

  Subclasses must implement these abstract methods:
    - _get_domain(): Return the keyring domain name for this config
    - _prompt_for_credentials(): Handle interactive credential input
    - _clear_credentials_impl(): Clear credential attributes from memory
    - _verify_exists_impl(): Check if credentials exist
    - save(): Save credentials to keyring
    - load(): Load credentials from keyring

  Attributes:
    domain: Keyring service name
    kr: Reference to the active keyring backend
  """

  # Class variable for test domain override
  _test_domain_override: str | None = None

  # ----------------------------------------------------------------------------
  def __init__(self) -> None:
    """Initialize Config and set up keyring access.

    Uses test domain override if set (for testing), otherwise uses
    subclass-provided default domain.
    """
    self.kr: Any = keyring.get_keyring()
    logger.debug(f'Using keyring backend: {type(self.kr).__name__}')

    # Use test domain if set (check on actual class, not BaseConfig)
    if self.__class__._test_domain_override:
      self.domain = self.__class__._test_domain_override
      logger.debug(f'Using test domain override: {self.domain}')
    else:
      self.domain = self._get_domain()
      logger.debug(f'Using default domain: {self.domain}')

  # ----------------------------------------------------------------------------
  @abstractmethod
  def _get_domain(self) -> str:
    """Return the keyring domain name for this config type.

    Returns:
      Domain name string (e.g., 'zpdatafetch', 'zrdatafetch')
    """

  # ----------------------------------------------------------------------------
  @abstractmethod
  def _prompt_for_credentials(self, **kwargs: Any) -> None:
    """Prompt user for credentials and set instance attributes.

    Called during setup() to interactively gather credentials from the user.
    Subclass must set appropriate credential attributes (username/password,
    authorization token, etc).

    Args:
      **kwargs: Optional pre-provided credential values to use instead
                of prompting
    """

  # ----------------------------------------------------------------------------
  @abstractmethod
  def _clear_credentials_impl(self) -> None:
    """Clear credential attributes from memory.

    Subclass implementation must overwrite credential attributes with
    placeholder values and then clear them.

    SECURITY: Python strings are immutable, so overwriting and clearing
    provides best-effort protection. For higher security requirements,
    consider using separate processes with memory protection.
    """

  # ----------------------------------------------------------------------------
  @abstractmethod
  def _verify_exists_impl(self) -> bool:
    """Check if credentials are set and valid.

    Returns:
      True if all required credentials are set, False otherwise
    """

  # ----------------------------------------------------------------------------
  @abstractmethod
  def save(self) -> None:
    """Save credentials to the system keyring.

    Subclass must implement to save all credential attributes to keyring
    using the configured domain.
    """

  # ----------------------------------------------------------------------------
  @abstractmethod
  def load(self) -> None:
    """Load credentials from the system keyring.

    Subclass must implement to load all credential attributes from keyring
    using the configured domain.
    """

  # ----------------------------------------------------------------------------
  def set_keyring(self, kr: KeyringBackend) -> None:
    """Set a custom keyring backend.

    Args:
      kr: Keyring backend instance (e.g., PlaintextKeyring for testing)
    """
    logger.debug(f'Setting custom keyring backend: {type(kr).__name__}')
    keyring.set_keyring(kr)

  # ----------------------------------------------------------------------------
  def replace_domain(self, domain: str) -> None:
    """Change the keyring service domain.

    Args:
      domain: New domain name to use for keyring operations
    """
    logger.debug(f'Changing domain from {self.domain} to {domain}')
    self.domain = domain

  # ----------------------------------------------------------------------------
  def setup(self, **kwargs: Any) -> None:
    """Configure credentials interactively or programmatically.

    If credentials are not provided via kwargs, prompts the user interactively.
    Saves credentials to keyring after collection.

    Args:
      **kwargs: Optional pre-provided credential values (varies by subclass)
    """
    logger.info('Setting up credentials')
    self._prompt_for_credentials(**kwargs)
    self.save()
    logger.info('Credentials setup completed')

  # ----------------------------------------------------------------------------
  def clear_credentials(self) -> None:
    """Securely clear credentials from memory.

    Overwrites credentials with placeholder values before clearing.
    This reduces the risk of credential recovery from memory dumps.

    SECURITY NOTE:
      Python strings are immutable, so this provides best-effort protection.
      For applications requiring higher security, use dedicated processes with
      memory protection or containers with appropriate isolation.
    """
    logger.debug('Clearing credentials from memory')
    self._clear_credentials_impl()
    logger.debug('Credentials cleared from memory')

  # ----------------------------------------------------------------------------
  def verify_credentials_exist(self) -> bool:
    """Verify that credentials are configured.

    Checks if all required credentials are present without exposing them.
    This is a safer alternative to dumping credentials for verification.

    Returns:
      True if all required credentials are set, False otherwise
    """
    logger.debug('Checking if credentials exist')
    return self._verify_exists_impl()
