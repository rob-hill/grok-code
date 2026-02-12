"""
Bash command execution tool with sandboxing.

CRITICAL: Integrates with CommandSandbox for safety.
"""
import os
from typing import Dict, Any, Optional
from tools.base import Tool
from safety.sandbox import CommandSandbox
from safety.permissions import PermissionManager


class BashTool(Tool):
    """
    Execute bash commands with safety checks.

    REQUIRES: CommandSandbox and PermissionManager for safety.
    """

    def __init__(self, sandbox: CommandSandbox, permission_manager: PermissionManager):
        """
        Initialize BashTool with safety components.

        Args:
            sandbox: CommandSandbox instance
            permission_manager: PermissionManager instance
        """
        super().__init__(
            name="bash",
            description="Execute a bash command in the working directory with safety checks",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (default: 30, max: 300)"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional, default: current directory)"
                    }
                },
                "required": ["command"]
            }
        )
        self.sandbox = sandbox
        self.permission_manager = permission_manager

    def execute(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute bash command with safety checks.

        Args:
            command: Command to execute
            timeout: Timeout in seconds
            cwd: Working directory

        Returns:
            Dict with success, stdout, stderr, returncode
        """
        try:
            # Validate command safety
            risk_level, error = self.sandbox.validate_command(command)

            # Block dangerous commands
            if risk_level == "blocked":
                return {
                    "success": False,
                    "error": error
                }

            # Request permission for risky commands
            if risk_level == "risky":
                details = {
                    "command": command,
                    "risk_level": "risky",
                    "working_directory": cwd or os.getcwd()
                }

                approved = self.permission_manager.request_permission(
                    operation="bash",
                    details=details
                )

                if not approved:
                    return {
                        "success": False,
                        "error": "Permission denied by user"
                    }

            # Set working directory
            work_dir = cwd if cwd else os.getcwd()
            work_dir = os.path.abspath(os.path.expanduser(work_dir))

            # Limit timeout
            timeout = min(timeout, 300)  # Max 5 minutes

            # Execute command
            stdout, stderr, returncode = self.sandbox.execute_safe(
                command=command,
                cwd=work_dir,
                timeout=timeout
            )

            return {
                "success": True,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode,
                "command": command
            }

        except Exception as e:
            error_msg = str(e)
            return {
                "success": False,
                "error": error_msg,
                "command": command
            }
