"""
Command sandboxing for safe bash execution.

CRITICAL SAFETY: Classifies commands and prevents destructive operations.
"""
import subprocess
import re
import shlex
from typing import Tuple
from safety.audit import get_audit_logger


class CommandSandbox:
    """
    Sandbox for executing bash commands safely.

    Classifies commands as safe, risky, or blocked.
    Executes commands with timeout and output limits.
    """

    # Commands that are ALWAYS blocked (destructive)
    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s+/",  # rm -rf /
        r"rm\s+-rf\s+/\*",  # rm -rf /*
        r"dd\s+if=.*of=/dev/",  # dd to device
        r"mkfs\.",  # Format filesystem
        r":\(\)\{.*\|\:.*\}\;",  # Fork bomb
        r"chmod\s+-R\s+777\s+/",  # Chmod root
        r">\s*/dev/sd",  # Write to disk device
        r"shred\s+",  # Secure delete
        r"fdisk\s+",  # Partition editor
        r"parted\s+",  # Partition editor
        r"mkswap\s+",  # Create swap
        r"swapon\s+",  # Enable swap
        r"swapoff\s+",  # Disable swap
        r"reboot",  # System reboot
        r"shutdown",  # System shutdown
        r"halt",  # System halt
        r"init\s+0",  # Shutdown
        r"init\s+6",  # Reboot
    ]

    # Commands that need user approval (risky but sometimes necessary)
    RISKY_COMMANDS = {
        "rm",  # Delete files
        "mv",  # Move files
        "git push",  # Push to remote
        "git force",  # Force operations
        "npm install",  # Install packages
        "pip install",  # Install packages
        "brew install",  # Install packages
        "apt install",  # Install packages
        "yum install",  # Install packages
        "chmod",  # Change permissions
        "chown",  # Change ownership
        "curl",  # Download (could download malware)
        "wget",  # Download
        "docker",  # Docker operations
        "kubectl",  # Kubernetes operations
    }

    # Commands that are safe to auto-approve
    SAFE_COMMANDS = {
        "ls",
        "cat",
        "head",
        "tail",
        "grep",
        "find",
        "git status",
        "git log",
        "git diff",
        "git show",
        "git branch",
        "pwd",
        "echo",
        "python --version",
        "python -m",
        "pytest",
        "node --version",
        "npm --version",
        "which",
        "whoami",
        "date",
        "env",
        "printenv",
    }

    @staticmethod
    def validate_command(command: str) -> Tuple[str, str]:
        """
        Validate a command for safety.

        Args:
            command: Command string to validate

        Returns:
            Tuple of (risk_level, error_message)
            - risk_level: "safe", "risky", or "blocked"
            - error_message: Error message if blocked, empty otherwise
        """
        # Check for blocked patterns
        for pattern in CommandSandbox.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                # Log blocked command attempt
                audit_logger = get_audit_logger()
                audit_logger.log_blocked_operation(
                    "bash_command",
                    f"Matched blocked pattern: {pattern}",
                    {"command": command}
                )
                return "blocked", (
                    f"Command blocked for safety: '{command}'. "
                    "This command is destructive and cannot be executed."
                )

        # Extract first command (before pipes or &&)
        first_cmd = command.split("|")[0].split("&&")[0].split(";")[0].strip()
        cmd_name = first_cmd.split()[0] if first_cmd else ""

        # Check if it's a safe command
        for safe_cmd in CommandSandbox.SAFE_COMMANDS:
            if first_cmd.startswith(safe_cmd):
                return "safe", ""

        # Check if it's a risky command
        for risky_cmd in CommandSandbox.RISKY_COMMANDS:
            if risky_cmd in command:
                return "risky", ""

        # Unknown commands default to risky (safer)
        return "risky", ""

    @staticmethod
    def execute_safe(
        command: str,
        cwd: str,
        timeout: int = 30,
        max_output_size: int = 100000
    ) -> Tuple[str, str, int]:
        """
        Execute a command safely with timeout and output limits.

        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Timeout in seconds
            max_output_size: Maximum output size in bytes

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            Exception: If timeout exceeded
        """
        try:
            # SECURITY: Use shlex.split() and shell=False to prevent command injection
            # This prevents shell metacharacter attacks (;, &&, ||, etc.)
            try:
                cmd_list = shlex.split(command)
            except ValueError as e:
                raise Exception(f"Invalid command syntax: {e}")

            result = subprocess.run(
                cmd_list,
                shell=False,  # CRITICAL: Prevents shell injection attacks
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            stdout = result.stdout
            stderr = result.stderr

            # Limit output size
            if len(stdout) > max_output_size:
                stdout = stdout[:max_output_size] + "\n... [output truncated]"
            if len(stderr) > max_output_size:
                stderr = stderr[:max_output_size] + "\n... [output truncated]"

            return stdout, stderr, result.returncode

        except subprocess.TimeoutExpired:
            raise Exception(
                f"Command timed out after {timeout} seconds. "
                "The command may be stuck or taking too long."
            )
        except Exception as e:
            raise Exception(f"Command execution failed: {e}")
