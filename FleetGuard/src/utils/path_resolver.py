"""
Smart path resolver that works in any environment.
Always resolves paths relative to package root.

This module provides intelligent path resolution that works consistently
across different environments (local development, Streamlit Cloud, tests,
Docker containers, etc.). It automatically finds the FleetGuard package
root and resolves all paths relative to it, eliminating common path-related
bugs.

Key Features:
- Multiple fallback strategies for finding package root
- Works in any directory structure
- Eliminates os.getcwd() issues
- Helper methods for common path patterns
- Thread-safe singleton pattern

Author: FleetGuardAI Team
Date: December 2025
"""

from pathlib import Path
import sys
from typing import Optional


class PathResolver:
    """Resolve paths relative to FleetGuard package root.

    This class finds the FleetGuard package root directory using multiple
    strategies and provides methods to resolve paths relative to it. This
    ensures paths work consistently regardless of:
    - Current working directory
    - How the application was launched
    - Deployment environment (local vs cloud)

    The resolver uses these strategies in order:
    1. Find from current file location (src/utils/path_resolver.py)
    2. Search sys.path for FleetGuard directory
    3. Search upward from current working directory
    4. Fallback to current working directory

    Attributes:
        _root: Path object pointing to FleetGuard package root directory

    Example:
        >>> from src.utils.path_resolver import path_resolver
        >>> # Get absolute path to any file
        >>> db_path = path_resolver.get_db_path('fleet.db')
        >>> print(db_path)  # /path/to/FleetGuard/data/database/fleet.db
        >>> # Get path to data file
        >>> csv_path = path_resolver.get_path('data/processed/results.csv')
        >>> df = pd.read_csv(csv_path)
    """

    _instance: Optional['PathResolver'] = None
    _root: Optional[Path] = None

    def __new__(cls):
        """Create or return existing singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize path resolver by finding package root."""
        self._root = self._find_package_root()

    def _find_package_root(self) -> Path:
        """Find FleetGuard package root directory using multiple strategies.

        Returns:
            Path object pointing to FleetGuard root directory

        Strategy details:
            1. From file location: Go up from src/utils/path_resolver.py
            2. From sys.path: Search for directory named 'FleetGuard'
            3. From cwd: Search upward in directory tree
            4. Fallback: Use current working directory
        """
        # Strategy 1: From this file's location
        # This file is at: FleetGuard/src/utils/path_resolver.py
        # So go up 3 levels to reach FleetGuard/
        try:
            current_file = Path(__file__).resolve()
            # Go up from src/utils/path_resolver.py to FleetGuard/
            package_root = current_file.parent.parent.parent

            # Verify it's the right directory by checking for main.py
            if (package_root / 'main.py').exists():
                return package_root
        except Exception:
            pass

        # Strategy 2: Search sys.path for FleetGuard directory
        try:
            for path_str in sys.path:
                candidate = Path(path_str)
                if candidate.name == 'FleetGuard' and (candidate / 'main.py').exists():
                    return candidate
        except Exception:
            pass

        # Strategy 3: Search upward from current working directory
        try:
            cwd = Path.cwd()

            # Check if cwd itself is FleetGuard
            if cwd.name == 'FleetGuard' and (cwd / 'main.py').exists():
                return cwd

            # Search upward in directory tree
            for parent in [cwd] + list(cwd.parents):
                # Check if this directory contains FleetGuard subdirectory
                fleetguard_subdir = parent / 'FleetGuard'
                if fleetguard_subdir.exists() and (fleetguard_subdir / 'main.py').exists():
                    return fleetguard_subdir

                # Check if this directory IS FleetGuard
                if parent.name == 'FleetGuard' and (parent / 'main.py').exists():
                    return parent
        except Exception:
            pass

        # Strategy 4: Fallback to current working directory
        # This might not be ideal, but it's better than crashing
        return Path.cwd()

    def get_path(self, relative_path: str) -> Path:
        """Convert relative path to absolute path from package root.

        Args:
            relative_path: Path relative to FleetGuard root (e.g., 'data/fleet.db')

        Returns:
            Absolute Path object

        Example:
            >>> path = path_resolver.get_path('data/processed/results.csv')
            >>> print(path)  # /abs/path/to/FleetGuard/data/processed/results.csv
            >>> print(path.exists())  # True or False
        """
        return (self._root / relative_path).resolve()

    def get_data_path(self, filename: str) -> Path:
        """Get path in data directory.

        Convenience method for files in the data/ directory.

        Args:
            filename: Filename or path within data/ directory

        Returns:
            Absolute Path object

        Example:
            >>> path = path_resolver.get_data_path('processed/fleet_data.csv')
            >>> # Equivalent to: path_resolver.get_path('data/processed/fleet_data.csv')
        """
        return self.get_path(f'data/{filename}')

    def get_db_path(self, db_name: str = 'fleet.db') -> Path:
        """Get database file path.

        Convenience method for database files in data/database/ directory.

        Args:
            db_name: Database filename (default: 'fleet.db')

        Returns:
            Absolute Path object

        Example:
            >>> fleet_db = path_resolver.get_db_path('fleet.db')
            >>> users_db = path_resolver.get_db_path('users.db')
        """
        return self.get_path(f'data/database/{db_name}')

    def get_model_path(self, filename: str) -> Path:
        """Get path in models directory.

        Convenience method for ML model files.

        Args:
            filename: Model filename

        Returns:
            Absolute Path object

        Example:
            >>> model_path = path_resolver.get_model_path('gradient_boost.pkl')
            >>> metadata_path = path_resolver.get_model_path('model_metadata.json')
        """
        return self.get_path(f'models/{filename}')

    def get_report_path(self, filename: str) -> Path:
        """Get path in reports directory.

        Convenience method for report files.

        Args:
            filename: Report filename

        Returns:
            Absolute Path object

        Example:
            >>> report_path = path_resolver.get_report_path('evaluation.md')
            >>> metrics_path = path_resolver.get_report_path('metrics.json')
        """
        return self.get_path(f'reports/{filename}')

    def get_src_path(self, filename: str) -> Path:
        """Get path in src directory.

        Convenience method for source code files.

        Args:
            filename: Source filename or path within src/

        Returns:
            Absolute Path object

        Example:
            >>> engine_path = path_resolver.get_src_path('ai_engine.py')
            >>> utils_path = path_resolver.get_src_path('utils/helpers.py')
        """
        return self.get_path(f'src/{filename}')

    @property
    def root(self) -> Path:
        """Return package root directory.

        Returns:
            Path object pointing to FleetGuard root

        Example:
            >>> root = path_resolver.root
            >>> print(root)  # /path/to/FleetGuard
            >>> print(list(root.iterdir()))  # List all files/dirs in root
        """
        return self._root

    def is_valid_root(self) -> bool:
        """Check if the found root directory is valid.

        A valid root should contain main.py and src/ directory.

        Returns:
            True if root is valid, False otherwise

        Example:
            >>> if path_resolver.is_valid_root():
            ...     print("FleetGuard root found successfully")
        """
        return (
            self._root.exists() and
            (self._root / 'main.py').exists() and
            (self._root / 'src').exists()
        )

    def relative_to_root(self, absolute_path: Path) -> Optional[Path]:
        """Convert absolute path to path relative to package root.

        Args:
            absolute_path: Absolute path to convert

        Returns:
            Path relative to root, or None if path is not under root

        Example:
            >>> abs_path = Path('/full/path/to/FleetGuard/data/fleet.db')
            >>> rel_path = path_resolver.relative_to_root(abs_path)
            >>> print(rel_path)  # data/fleet.db
        """
        try:
            return Path(absolute_path).relative_to(self._root)
        except ValueError:
            return None  # Path is not under root

    def __repr__(self) -> str:
        """String representation for debugging."""
        valid = "valid" if self.is_valid_root() else "invalid"
        return f"<PathResolver(root='{self._root}', status='{valid}')>"

    def __str__(self) -> str:
        """Human-readable string."""
        return str(self._root)


# Singleton instance for global access
path_resolver = PathResolver()
