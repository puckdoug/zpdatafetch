"""Shared utilities for zpdatafetch and zrdatafetch packages.

This module provides common functionality used by both the zpdatafetch
and zrdatafetch packages to eliminate code duplication.

Note: To avoid circular imports, import specific modules directly:
  from shared.exceptions import NetworkError
  from shared.config import BaseConfig
  from shared.http_client import BaseHTTPClient
  from shared.cli import create_base_parser
  from shared.logging import get_logger
"""
