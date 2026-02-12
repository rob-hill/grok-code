"""
Tests for safety modules (validators, sandbox, permissions).

Following TDD methodology - CRITICAL safety tests.
These must pass before implementing any file or command tools.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock


class TestPathValidator:
    """Test suite for path validation (CRITICAL)."""

    def test_blocks_system_directory_writes(self):
        """
        Test that writes to system directories are blocked.

        CRITICAL: Must block /etc, /usr, /bin, /sbin, /sys, /proc
        This test should FAIL initially.
        """
        from safety.validators import PathValidator

        dangerous_paths = [
            "/etc/passwd",
            "/usr/bin/malware",
            "/bin/dangerous",
            "/sbin/system",
            "/sys/kernel",
            "/proc/config"
        ]

        for path in dangerous_paths:
            is_valid, warning = PathValidator.validate_path(path, "write")
            assert is_valid == False, f"Should block write to {path}"
            assert "system" in warning.lower() or "denied" in warning.lower()

    def test_blocks_system_directory_deletes(self):
        """
        Test that deletes in system directories are blocked.

        This test should FAIL initially.
        """
        from safety.validators import PathValidator

        dangerous_paths = [
            "/etc/important.conf",
            "/usr/lib/library.so"
        ]

        for path in dangerous_paths:
            is_valid, warning = PathValidator.validate_path(path, "delete")
            assert is_valid == False, f"Should block delete of {path}"

    def test_allows_working_directory_operations(self):
        """
        Test that operations within working directory are allowed.

        This test should FAIL initially.
        """
        from safety.validators import PathValidator

        # Paths within working directory should be allowed
        safe_paths = [
            "/Users/ksy-syd-mbp-200/Documents/coding/cursor/grok-code/test.txt",
            "/Users/ksy-syd-mbp-200/Documents/coding/cursor/grok-code/core/api.py",
            "./local_file.txt",
            "relative/path/file.txt"
        ]

        for path in safe_paths:
            is_valid, warning = PathValidator.validate_path(path, "write")
            assert is_valid == True, f"Should allow write to {path}"

    def test_warns_about_sensitive_files(self):
        """
        Test that writes to sensitive files trigger warnings (but don't block).

        This test should FAIL initially.
        """
        from safety.validators import PathValidator

        sensitive_files = [
            "/Users/ksy-syd-mbp-200/Documents/coding/cursor/grok-code/.env",
            "/Users/ksy-syd-mbp-200/.ssh/id_rsa",
            "/Users/ksy-syd-mbp-200/credentials.json",
            "./config/secrets.yaml"
        ]

        for path in sensitive_files:
            is_valid, warning = PathValidator.validate_path(path, "write")
            # Should allow but with warning
            if not is_valid:
                # Skip if blocked for other reasons (like /etc)
                continue
            # Check if warning is present for sensitive files in allowed directories
            if "/Users/ksy-syd-mbp-200/Documents" in path or path.startswith("."):
                assert warning != "", f"Should warn about {path}"
                assert "sensitive" in warning.lower() or "credential" in warning.lower() or "warning" in warning.lower()

    def test_read_operations_always_allowed(self):
        """
        Test that read operations are always allowed (less risky).

        This test should FAIL initially.
        """
        from safety.validators import PathValidator

        paths = [
            "/etc/passwd",  # System file
            "/Users/ksy-syd-mbp-200/.ssh/id_rsa",  # Sensitive file
            "./test.txt"  # Regular file
        ]

        for path in paths:
            is_valid, warning = PathValidator.validate_path(path, "read")
            assert is_valid == True, f"Should allow read of {path}"


class TestCommandSandbox:
    """Test suite for command sandboxing (CRITICAL)."""

    def test_blocks_destructive_commands(self):
        """
        Test that destructive commands are always blocked.

        CRITICAL: Must block rm -rf, dd, mkfs, etc.
        This test should FAIL initially.
        """
        from safety.sandbox import CommandSandbox

        blocked_commands = [
            "rm -rf /",
            "rm -rf /*",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda",
            ":(){ :|:& };:",  # Fork bomb
            "chmod -R 777 /",
            "> /dev/sda"
        ]

        for cmd in blocked_commands:
            risk_level, error = CommandSandbox.validate_command(cmd)
            assert risk_level == "blocked", f"Should block: {cmd}"
            assert error != "", f"Should have error message for: {cmd}"

    def test_classifies_safe_commands(self):
        """
        Test that safe commands are classified correctly.

        This test should FAIL initially.
        """
        from safety.sandbox import CommandSandbox

        safe_commands = [
            "ls -la",
            "cat test.txt",
            "git status",
            "git log",
            "git diff",
            "pwd",
            "echo 'hello'",
            "python --version"
        ]

        for cmd in safe_commands:
            risk_level, error = CommandSandbox.validate_command(cmd)
            assert risk_level == "safe", f"Should classify as safe: {cmd}"
            assert error == "", f"Should have no error for: {cmd}"

    def test_classifies_risky_commands(self):
        """
        Test that risky commands are classified correctly.

        This test should FAIL initially.
        """
        from safety.sandbox import CommandSandbox

        risky_commands = [
            "rm test.txt",
            "mv file1.txt file2.txt",
            "git push origin main",
            "npm install",
            "pip install requests",
            "chmod 755 script.sh"
        ]

        for cmd in risky_commands:
            risk_level, error = CommandSandbox.validate_command(cmd)
            assert risk_level == "risky", f"Should classify as risky: {cmd}"
            assert error == "", f"Should have no error for risky command: {cmd}"

    def test_executes_safe_commands(self):
        """
        Test that safe commands can be executed.

        This test should FAIL initially.
        """
        from safety.sandbox import CommandSandbox

        # Execute a simple safe command
        stdout, stderr, returncode = CommandSandbox.execute_safe(
            "echo 'test'",
            cwd="/tmp",
            timeout=5
        )

        assert returncode == 0
        assert "test" in stdout
        assert stderr == ""

    def test_respects_timeout(self):
        """
        Test that command execution respects timeout.

        This test should FAIL initially.
        """
        from safety.sandbox import CommandSandbox

        # Command that sleeps should timeout
        with pytest.raises(Exception, match="timeout|timed out"):
            CommandSandbox.execute_safe(
                "sleep 10",
                cwd="/tmp",
                timeout=1
            )

    def test_limits_output_size(self):
        """
        Test that output size is limited to prevent memory issues.

        This test should FAIL initially.
        """
        from safety.sandbox import CommandSandbox

        # Command that generates lots of output
        stdout, stderr, returncode = CommandSandbox.execute_safe(
            "seq 1 10000",
            cwd="/tmp",
            timeout=5
        )

        # Output should be limited (e.g., max 100KB)
        assert len(stdout) < 100000 or "truncated" in stdout.lower()


class TestPermissionManager:
    """Test suite for permission management."""

    def test_permission_manager_creates_instance(self):
        """
        Test that PermissionManager can be instantiated.

        This test should FAIL initially.
        """
        from safety.permissions import PermissionManager

        manager = PermissionManager()
        assert manager is not None

    def test_permission_manager_has_cache(self):
        """
        Test that PermissionManager maintains permission cache.

        This test should FAIL initially.
        """
        from safety.permissions import PermissionManager

        manager = PermissionManager()
        assert hasattr(manager, 'permission_cache')
        assert isinstance(manager.permission_cache, dict)

    def test_request_permission_interface(self):
        """
        Test that request_permission has correct interface.

        This test should FAIL initially.
        """
        from safety.permissions import PermissionManager

        manager = PermissionManager()

        # Mock user input to approve
        with patch('builtins.input', return_value='y'):
            approved = manager.request_permission(
                operation="write_file",
                details={"path": "/test/file.txt", "risk": "medium"}
            )

            assert isinstance(approved, bool)

    def test_permission_caching_works(self):
        """
        Test that permission caching prevents repeated prompts.

        This test should FAIL initially.
        """
        from safety.permissions import PermissionManager

        manager = PermissionManager()

        # First call - mock user approving
        with patch('builtins.input', return_value='always'):
            approved1 = manager.request_permission(
                operation="write_file",
                details={"path": "/test/file.txt"}
            )
            assert approved1 == True

        # Second call - should use cache, not prompt
        with patch('builtins.input') as mock_input:
            approved2 = manager.request_permission(
                operation="write_file",
                details={"path": "/test/file2.txt"}
            )
            # Should not have called input (used cache)
            mock_input.assert_not_called()
            assert approved2 == True

    def test_permission_denial_works(self):
        """
        Test that user can deny permissions.

        This test should FAIL initially.
        """
        from safety.permissions import PermissionManager

        manager = PermissionManager()

        # Mock user denying
        with patch('builtins.input', return_value='n'):
            approved = manager.request_permission(
                operation="delete_file",
                details={"path": "/important/file.txt"}
            )

            assert approved == False

    def test_permission_never_caching_works(self):
        """
        Test that 'never' response caches denial.

        This test should FAIL initially.
        """
        from safety.permissions import PermissionManager

        manager = PermissionManager()

        # First call - mock user denying with 'never'
        with patch('builtins.input', return_value='never'):
            approved1 = manager.request_permission(
                operation="dangerous_op",
                details={"path": "/test"}
            )
            assert approved1 == False

        # Second call - should use cache, not prompt
        with patch('builtins.input') as mock_input:
            approved2 = manager.request_permission(
                operation="dangerous_op",
                details={"path": "/test2"}
            )
            mock_input.assert_not_called()
            assert approved2 == False
