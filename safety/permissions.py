"""
Permission management for user approval of risky operations.

Implements permission requests with session caching.
"""
from typing import Dict, Any
from safety.audit import get_audit_logger


class PermissionManager:
    """
    Manages user permissions for risky operations.

    Requests user approval and caches decisions for the session.
    """

    def __init__(self):
        """Initialize permission manager with empty cache."""
        self.permission_cache: Dict[str, bool] = {}
        self.audit_logger = get_audit_logger()

    def request_permission(
        self,
        operation: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Request user permission for an operation.

        Args:
            operation: Operation type (e.g., "write_file", "bash", "delete_file")
            details: Details about the operation (path, command, risk level, etc.)

        Returns:
            True if approved, False if denied
        """
        # Check cache first
        if operation in self.permission_cache:
            cached_response = self.permission_cache[operation]
            # Log cached response
            self.audit_logger.log_permission_request(operation, cached_response, {"cached": True})
            return cached_response

        # Format permission request
        print("\n" + "=" * 60)
        print(f"⚠️  PERMISSION REQUIRED: {operation.upper().replace('_', ' ')}")
        print("=" * 60)

        # Display details
        for key, value in details.items():
            print(f"{key.capitalize()}: {value}")

        print("\nOptions:")
        print("  y     - Allow this operation")
        print("  n     - Deny this operation")
        print("  always - Always allow this type of operation (session)")
        print("  never  - Never allow this type of operation (session)")
        print("=" * 60)

        # Get user input
        while True:
            response = input("Allow? (y/n/always/never): ").strip().lower()

            if response in ['y', 'yes']:
                self.audit_logger.log_permission_request(operation, True, details)
                return True
            elif response in ['n', 'no']:
                self.audit_logger.log_permission_request(operation, False, details)
                return False
            elif response == 'always':
                # Cache approval for session
                self.permission_cache[operation] = True
                print(f"✓ '{operation}' will be auto-approved for this session.")
                self.audit_logger.log_permission_request(operation, True, {**details, "cached": "always"})
                return True
            elif response == 'never':
                # Cache denial for session
                self.permission_cache[operation] = False
                print(f"✗ '{operation}' will be auto-denied for this session.")
                self.audit_logger.log_permission_request(operation, False, {**details, "cached": "never"})
                return False
            else:
                print("Invalid response. Please enter y, n, always, or never.")

    def clear_cache(self):
        """Clear all cached permissions."""
        self.permission_cache.clear()

    def get_cache_status(self) -> Dict[str, bool]:
        """
        Get current cache status.

        Returns:
            Dict of operation -> allowed/denied
        """
        return self.permission_cache.copy()
