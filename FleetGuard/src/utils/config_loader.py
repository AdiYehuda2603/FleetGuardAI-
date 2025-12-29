"""
Unified configuration loader for both local and Streamlit Cloud environments.
Handles .env files (local) and Streamlit secrets (cloud) seamlessly.

This module provides a centralized configuration management system that:
- Automatically detects the runtime environment (local vs cloud)
- Loads configuration from .env files in local development
- Uses Streamlit secrets in cloud deployment
- Provides type-safe getter methods for different data types
- Implements singleton pattern for efficient resource usage

Author: FleetGuardAI Team
Date: December 2025
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class ConfigLoader:
    """Smart configuration loader with environment detection.

    This class implements a singleton pattern to ensure configuration
    is loaded only once per application lifecycle. It automatically
    detects whether the application is running locally or in Streamlit
    Cloud and loads configuration from the appropriate source.

    Attributes:
        _instance: Singleton instance
        _config: Dictionary storing all configuration values
        _source: String indicating configuration source ("streamlit_secrets" or "dotenv")

    Example:
        >>> from src.utils.config_loader import config
        >>> api_key = config.get("OPENAI_API_KEY")
        >>> port = config.get_int("EMAIL_IMAP_PORT", 993)
        >>> enabled = config.get_bool("EMAIL_FETCH_ENABLED", False)
    """

    _instance: Optional['ConfigLoader'] = None
    _config: dict = {}
    _source: str = "unknown"

    def __new__(cls):
        """Create or return existing singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from appropriate source.

        Priority order:
        1. Streamlit secrets (cloud environment)
        2. .env file (local development)
        3. Environment variables (fallback)
        """
        # Try Streamlit secrets first (cloud environment)
        try:
            if hasattr(st, 'secrets') and len(st.secrets) > 0:
                self._config = dict(st.secrets)
                self._source = "streamlit_secrets"
                return
        except Exception:
            pass  # Streamlit not initialized yet or no secrets

        # Fallback to .env file (local development)
        try:
            # Find .env file - go up from src/utils/ to FleetGuard/
            current_file = Path(__file__).resolve()
            env_path = current_file.parent.parent.parent / '.env'

            if env_path.exists():
                load_dotenv(env_path)
                self._source = "dotenv"
            else:
                # Try alternative path (from project root)
                alt_env_path = Path.cwd() / 'FleetGuard' / '.env'
                if alt_env_path.exists():
                    load_dotenv(alt_env_path)
                    self._source = "dotenv"
        except Exception:
            pass  # .env file not found or error loading

        # Store current environment variables
        self._config = dict(os.environ)

        if self._source == "unknown":
            self._source = "environment"

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value by key.

        This method tries multiple sources in order:
        1. Streamlit secrets (if available)
        2. Cached configuration dictionary
        3. Environment variables (fallback)
        4. Default value

        Args:
            key: Configuration key to retrieve
            default: Default value if key not found

        Returns:
            Configuration value as string, or default if not found

        Example:
            >>> api_key = config.get("OPENAI_API_KEY")
            >>> db_path = config.get("DATABASE_PATH", "data/database/fleet.db")
        """
        # Try Streamlit secrets first (highest priority)
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                value = st.secrets[key]
                return str(value) if value is not None else default
        except Exception:
            pass

        # Try cached config
        value = self._config.get(key)

        # Try environment variables as fallback
        if value is None:
            value = os.getenv(key)

        # Return value or default (don't return empty strings)
        return value if value else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value.

        Interprets various string representations as boolean:
        - True: 'true', '1', 'yes', 'on' (case-insensitive)
        - False: everything else

        Args:
            key: Configuration key to retrieve
            default: Default value if key not found

        Returns:
            Boolean value

        Example:
            >>> enabled = config.get_bool("EMAIL_FETCH_ENABLED", False)
            >>> debug = config.get_bool("DEBUG_MODE", False)
        """
        value = self.get(key, str(default))
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'on')

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value.

        Args:
            key: Configuration key to retrieve
            default: Default value if key not found or conversion fails

        Returns:
            Integer value

        Example:
            >>> port = config.get_int("EMAIL_IMAP_PORT", 993)
            >>> max_fetch = config.get_int("EMAIL_MAX_FETCH", 50)
        """
        try:
            value = self.get(key, str(default))
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value.

        Args:
            key: Configuration key to retrieve
            default: Default value if key not found or conversion fails

        Returns:
            Float value

        Example:
            >>> threshold = config.get_float("ANOMALY_THRESHOLD", 2.0)
        """
        try:
            value = self.get(key, str(default))
            return float(value)
        except (ValueError, TypeError):
            return default

    @property
    def source(self) -> str:
        """Return configuration source for debugging.

        Returns:
            One of: "streamlit_secrets", "dotenv", "environment", or "unknown"

        Example:
            >>> print(f"Config loaded from: {config.source}")
            Config loaded from: streamlit_secrets
        """
        return self._source

    def reload(self):
        """Force reload configuration from source.

        Useful when configuration changes at runtime (e.g., after
        updating .env file or Streamlit secrets).

        Example:
            >>> config.reload()
        """
        self._load_config()

    def has_key(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key to check

        Returns:
            True if key exists, False otherwise

        Example:
            >>> if config.has_key("OPENAI_API_KEY"):
            ...     print("API key configured")
        """
        return self.get(key) is not None

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<ConfigLoader(source='{self._source}', keys={len(self._config)})>"


# Singleton instance for global access
config = ConfigLoader()
