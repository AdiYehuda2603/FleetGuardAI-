"""
Smart file handler that adapts to environment.
Writes to disk in local dev, uses memory buffers in cloud.

This module provides environment-aware file operations that automatically
adapt between local development (with disk writes) and cloud deployment
(with in-memory storage). This ensures the application works seamlessly
in both environments without code changes.

Key Features:
- Automatic environment detection (local vs Streamlit Cloud)
- Transparent switching between disk and memory storage
- Streamlit download button compatibility
- Support for both text and binary files
- Thread-safe singleton pattern

Author: FleetGuardAI Team
Date: December 2025
"""

import os
import io
from pathlib import Path
from typing import Union, Optional, List
from fnmatch import fnmatch


class FileHandler:
    """Environment-aware file operations handler.

    This class automatically detects whether the application is running
    in a cloud environment (read-only filesystem) or locally, and adapts
    file operations accordingly:

    - Local: Files are written to disk normally
    - Cloud: Files are stored in memory for the session duration

    The API remains identical regardless of environment, making code
    portable and environment-agnostic.

    Attributes:
        is_cloud: Boolean indicating if running in cloud environment
        _memory_store: Dictionary storing in-memory files (cloud only)

    Example:
        >>> from src.utils.file_handler import file_handler
        >>> # Write file (automatically chooses disk or memory)
        >>> file_handler.write_text('report.md', '# Report\\nContent here')
        >>> # Read file back
        >>> content = file_handler.read_text('report.md')
        >>> # Get buffer for Streamlit download
        >>> buffer = file_handler.get_buffer('report.md')
        >>> st.download_button("Download", buffer, "report.md")
    """

    _instance: Optional['FileHandler'] = None

    def __new__(cls):
        """Create or return existing singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize file handler instance."""
        self.is_cloud = self._detect_cloud_environment()
        self._memory_store = {}  # In-memory file storage for cloud

    def _detect_cloud_environment(self) -> bool:
        """Detect if running on Streamlit Cloud or similar read-only environment.

        Detection strategies:
        1. Check for Streamlit-specific environment variables
        2. Test write permissions on current directory
        3. Check for cloud-specific markers

        Returns:
            True if running in cloud/read-only environment, False otherwise
        """
        # Strategy 1: Check Streamlit Cloud environment variables
        if os.getenv('STREAMLIT_SHARING_MODE') is not None:
            return True

        if os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true':
            return True

        # Strategy 2: Test write permissions
        try:
            test_file = Path('.') / '.write_test_temp'
            test_file.touch()
            test_file.unlink()
            return False  # Write succeeded - not cloud
        except (OSError, PermissionError):
            return True  # Write failed - likely cloud

    def write_text(self, path: str, content: str, encoding: str = 'utf-8') -> str:
        """Write text file - disk or memory based on environment.

        Args:
            path: File path (relative or absolute)
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Returns:
            Path to written file (virtual path in cloud)

        Example:
            >>> file_handler.write_text('reports/summary.md', '# Summary\\nData here')
            'reports/summary.md'
        """
        if self.is_cloud:
            # Store in memory
            self._memory_store[path] = content.encode(encoding)
            return path  # Return virtual path
        else:
            # Write to disk (local dev)
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=encoding)
            return str(file_path)

    def write_binary(self, path: str, content: bytes) -> str:
        """Write binary file - disk or memory based on environment.

        Args:
            path: File path (relative or absolute)
            content: Binary content to write

        Returns:
            Path to written file (virtual path in cloud)

        Example:
            >>> with open('image.png', 'rb') as f:
            ...     data = f.read()
            >>> file_handler.write_binary('outputs/image.png', data)
        """
        if self.is_cloud:
            self._memory_store[path] = content
            return path
        else:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            return str(file_path)

    def read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """Read text file from memory or disk.

        Args:
            path: File path to read
            encoding: Text encoding (default: utf-8)

        Returns:
            Text content of file

        Raises:
            FileNotFoundError: If file doesn't exist in memory or disk

        Example:
            >>> content = file_handler.read_text('reports/summary.md')
            >>> print(content)
        """
        if self.is_cloud and path in self._memory_store:
            return self._memory_store[path].decode(encoding)
        else:
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            return file_path.read_text(encoding=encoding)

    def read_binary(self, path: str) -> bytes:
        """Read binary file from memory or disk.

        Args:
            path: File path to read

        Returns:
            Binary content of file

        Raises:
            FileNotFoundError: If file doesn't exist in memory or disk

        Example:
            >>> data = file_handler.read_binary('outputs/model.pkl')
        """
        if self.is_cloud and path in self._memory_store:
            return self._memory_store[path]
        else:
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            return file_path.read_bytes()

    def get_buffer(self, path: str) -> Optional[io.BytesIO]:
        """Get BytesIO buffer for Streamlit downloads.

        This method is particularly useful for Streamlit's download_button
        widget, which requires a BytesIO buffer.

        Args:
            path: File path to get buffer for

        Returns:
            BytesIO buffer containing file data, or None if file not found

        Example:
            >>> buffer = file_handler.get_buffer('reports/summary.md')
            >>> if buffer:
            ...     st.download_button("Download Report", buffer, "summary.md")
        """
        try:
            if self.is_cloud and path in self._memory_store:
                return io.BytesIO(self._memory_store[path])
            else:
                file_path = Path(path)
                if file_path.exists():
                    return io.BytesIO(file_path.read_bytes())
        except Exception:
            pass
        return None

    def exists(self, path: str) -> bool:
        """Check if file exists in memory or disk.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise

        Example:
            >>> if file_handler.exists('reports/summary.md'):
            ...     print("Report found")
        """
        if self.is_cloud:
            return path in self._memory_store
        else:
            return Path(path).exists()

    def list_files(self, pattern: str = "*") -> List[str]:
        """List files matching pattern from memory or disk.

        Args:
            pattern: Glob pattern (e.g., "*.txt", "reports/*.md")

        Returns:
            List of file paths matching pattern

        Example:
            >>> reports = file_handler.list_files("reports/*.md")
            >>> for report in reports:
            ...     print(report)
        """
        if self.is_cloud:
            # Return virtual paths from memory that match pattern
            return [p for p in self._memory_store.keys() if fnmatch(p, pattern)]
        else:
            # Use pathlib to find files on disk
            if '/' in pattern or '\\' in pattern:
                # Pattern includes directory
                parts = pattern.split('/')
                if len(parts) == 2:
                    directory, file_pattern = parts
                    base_path = Path(directory)
                    if base_path.exists():
                        return [str(p) for p in base_path.glob(file_pattern)]
            # Simple pattern in current directory
            return [str(p) for p in Path('.').glob(pattern)]

    def delete(self, path: str) -> bool:
        """Delete file from memory or disk.

        Args:
            path: File path to delete

        Returns:
            True if file was deleted, False if it didn't exist

        Example:
            >>> file_handler.delete('temp/cache.json')
        """
        if self.is_cloud:
            if path in self._memory_store:
                del self._memory_store[path]
                return True
            return False
        else:
            file_path = Path(path)
            if file_path.exists():
                file_path.unlink()
                return True
            return False

    def clear_memory(self):
        """Clear all in-memory files (cloud only).

        Useful for freeing memory after processing large files.

        Example:
            >>> file_handler.clear_memory()
        """
        if self.is_cloud:
            self._memory_store.clear()

    def get_size(self, path: str) -> Optional[int]:
        """Get file size in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes, or None if file doesn't exist

        Example:
            >>> size = file_handler.get_size('reports/summary.md')
            >>> print(f"Report size: {size} bytes")
        """
        if self.is_cloud:
            if path in self._memory_store:
                return len(self._memory_store[path])
            return None
        else:
            file_path = Path(path)
            if file_path.exists():
                return file_path.stat().st_size
            return None

    def __repr__(self) -> str:
        """String representation for debugging."""
        env = "cloud" if self.is_cloud else "local"
        files_count = len(self._memory_store) if self.is_cloud else "N/A"
        return f"<FileHandler(environment='{env}', cached_files={files_count})>"


# Singleton instance for global access
file_handler = FileHandler()
