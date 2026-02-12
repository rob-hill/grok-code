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

        # Convert to absolute path and resolve symlinks for security
        try:
            # First expand user and make absolute
            abs_path = os.path.abspath(os.path.expanduser(path))

            # SECURITY: Check BEFORE symlink resolution (catches /etc even if it's a symlink)
            for dangerous_path in PathValidator.DANGEROUS_PATHS:
                if abs_path.startswith(dangerous_path + "/") or abs_path == dangerous_path:
                    return False, (
                        f"Access denied: Cannot {operation} in system directory {dangerous_path}. "
                        "This operation is blocked for safety."
                    )

            # Resolve symlinks to prevent symlink attacks
            # For existing files/directories, resolve the full path
            # For non-existent files, resolve the parent directory
            if os.path.exists(abs_path):
                resolved_path = os.path.realpath(abs_path)
            else:
                # Resolve parent directory, then append filename
                parent = os.path.dirname(abs_path)
                filename = os.path.basename(abs_path)
                if os.path.exists(parent):
                    resolved_path = os.path.join(os.path.realpath(parent), filename)
                else:
                    resolved_path = abs_path

            # SECURITY: Check AFTER symlink resolution (catches /private/etc on macOS)
            for dangerous_path in PathValidator.DANGEROUS_PATHS:
                if resolved_path.startswith(dangerous_path + "/") or resolved_path == dangerous_path:
                    return False, (
                        f"Access denied: Cannot {operation} in system directory {dangerous_path}. "
                        "This operation is blocked for safety."
                    )

            # Also check for /private/* paths on macOS
            if resolved_path.startswith("/private/etc/") or resolved_path.startswith("/private/usr/"):
                return False, (
                    f"Access denied: Cannot {operation} in system directory. "
                    "This operation is blocked for safety."
                )

            # Use resolved path for further checks
            abs_path = resolved_path

        except Exception as e:
            return False, f"Invalid path: {e}"

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
