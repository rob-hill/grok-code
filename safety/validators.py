"""
Path validation for file operations.

CRITICAL SAFETY: Blocks dangerous file operations before they happen.
"""
import os
from pathlib import Path
from typing import Tuple


class PathValidator:
    """
    Validates file paths for safety.

    Blocks operations on system directories and warns about sensitive files.
    """

    # System directories that should NEVER be modified
    DANGEROUS_PATHS = [
        "/etc",
        "/usr",
        "/bin",
        "/sbin",
        "/sys",
        "/proc",
        "/boot",
        "/dev",
        "/lib",
        "/lib64",
        "/var/lib",
        "/System",  # macOS
        "/Library",  # macOS system library
    ]

    # File patterns that are sensitive (warn but allow)
    SENSITIVE_PATTERNS = [
        ".env",
        "credentials.json",
        "credentials.yaml",
        "secrets.yaml",
        "secrets.json",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        ".pem",
        ".key",
        "config/secrets",
        "token",
        "password",
    ]

    @staticmethod
    def validate_path(path: str, operation: str) -> Tuple[bool, str]:
        """
        Validate a file path for safety.

        Args:
            path: File path to validate
            operation: Operation type ("read", "write", "delete")

        Returns:
            Tuple of (is_valid, warning_message)
            - is_valid: True if operation allowed, False if blocked
            - warning_message: Warning/error message (empty string if no issues)
        """
        # Read operations are always allowed (less risky)
        if operation == "read":
            return True, ""

        # Convert to absolute path for checking
        try:
            abs_path = os.path.abspath(os.path.expanduser(path))
        except Exception as e:
            return False, f"Invalid path: {e}"

        # Check for system directory access
        for dangerous_path in PathValidator.DANGEROUS_PATHS:
            if abs_path.startswith(dangerous_path + "/") or abs_path == dangerous_path:
                return False, (
                    f"Access denied: Cannot {operation} in system directory {dangerous_path}. "
                    "This operation is blocked for safety."
                )

        # Check for sensitive files (warn but allow)
        path_lower = abs_path.lower()
        for pattern in PathValidator.SENSITIVE_PATTERNS:
            if pattern.lower() in path_lower:
                # Get just the filename for clearer warning
                filename = os.path.basename(abs_path)
                return True, (
                    f"⚠️  WARNING: {operation.capitalize()}ing sensitive file '{filename}'. "
                    "This file may contain credentials or secrets."
                )

        # Path is safe
        return True, ""

    @staticmethod
    def is_within_directory(path: str, directory: str) -> bool:
        """
        Check if path is within a directory.

        Args:
            path: Path to check
            directory: Directory to check within

        Returns:
            True if path is within directory
        """
        try:
            abs_path = os.path.abspath(os.path.expanduser(path))
            abs_dir = os.path.abspath(os.path.expanduser(directory))
            return abs_path.startswith(abs_dir + os.sep) or abs_path == abs_dir
        except Exception:
            return False
