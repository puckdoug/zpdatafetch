"""Custom exceptions for zpdatafetch module.

Provides typed exceptions for different error conditions when interacting
with the Zwiftpower API. These are aliases to the shared exception classes
for backward compatibility.
"""

import sys
from pathlib import Path

_parent_dir = str(Path(__file__).parent.parent)
if _parent_dir not in sys.path:
  sys.path.insert(0, _parent_dir)

from exceptions import AuthenticationError, ConfigError, NetworkError  # noqa: E402

# Backward-compatible aliases for zpdatafetch
ZPAuthenticationError = AuthenticationError
ZPNetworkError = NetworkError
ZPConfigError = ConfigError
