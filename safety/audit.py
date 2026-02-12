"""
Audit logging for security-sensitive operations.

Logs all risky operations for security review and debugging.
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any


class AuditLogger:
    """
    Audit logger for security-sensitive operations.

    Logs operations like file writes, command execution, and permission requests.
    """

    def __init__(self, log_file: str = None):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file (default: ~/.grok-code/audit.log)
        """
        if log_file is None:
            log_dir = os.path.expanduser("~/.grok-code")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "audit.log")

        self.log_file = log_file

        # Configure logging
        self.logger = logging.getLogger("grok-code-audit")
        self.logger.setLevel(logging.INFO)

        # File handler
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)

        # Format: timestamp | level | operation | details
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def log_operation(
        self,
        operation: str,
        details: Dict[str, Any],
        risk_level: str = "INFO"
    ) -> None:
        """
        Log a security-sensitive operation.

        Args:
            operation: Operation type (e.g., "write_file", "bash", "permission_request")
            details: Dictionary of operation details
            risk_level: Risk level (INFO, WARNING, ERROR)
        """
        # Format details as key=value pairs
        detail_str = " | ".join(f"{k}={v}" for k, v in details.items())
        log_msg = f"{operation} | {detail_str}"

        # Log at appropriate level
        if risk_level == "ERROR":
            self.logger.error(log_msg)
        elif risk_level == "WARNING":
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)

    def log_permission_request(
        self,
        operation: str,
        approved: bool,
        details: Dict[str, Any]
    ) -> None:
        """Log a permission request and response."""
        details["approved"] = approved
        risk = "WARNING" if not approved else "INFO"
        self.log_operation(f"permission_request:{operation}", details, risk)

    def log_blocked_operation(
        self,
        operation: str,
        reason: str,
        details: Dict[str, Any]
    ) -> None:
        """Log a blocked operation (CRITICAL)."""
        details["reason"] = reason
        self.log_operation(f"blocked:{operation}", details, "ERROR")

    def get_log_path(self) -> str:
        """Get the path to the audit log file."""
        return self.log_file


# Global audit logger instance
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    return _audit_logger
