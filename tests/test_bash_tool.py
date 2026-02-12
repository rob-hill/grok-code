"""
Tests for BashTool with command sandboxing.

Following TDD methodology - CRITICAL safety integration.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock


class TestBashTool:
    """Test suite for BashTool with safety integration."""

    def test_bash_tool_exists(self):
        """
        Test that BashTool can be imported and instantiated.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        assert tool is not None
        assert tool.name == "bash"

    def test_bash_executes_safe_command(self):
        """
        Test that BashTool executes safe commands without permission.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        # Execute safe command
        result = tool.execute(command="echo 'hello world'")

        assert result["success"] == True
        assert "hello world" in result["stdout"]
        assert result["returncode"] == 0

    def test_bash_blocks_destructive_commands(self):
        """
        Test that BashTool blocks destructive commands.

        CRITICAL: Must use CommandSandbox to block.
        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        # Try destructive command
        result = tool.execute(command="rm -rf /")

        assert result["success"] == False
        assert "blocked" in result["error"].lower()

    def test_bash_requests_permission_for_risky_commands(self):
        """
        Test that BashTool requests permission for risky commands.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        # Mock user denying permission
        with patch.object(permission_mgr, 'request_permission', return_value=False):
            result = tool.execute(command="rm test.txt")

            assert result["success"] == False
            assert "permission" in result["error"].lower() or "denied" in result["error"].lower()

    def test_bash_executes_risky_command_with_permission(self):
        """
        Test that BashTool executes risky commands when permission granted.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager
        import tempfile

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        # Create temp file to remove
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            # Mock user approving permission
            with patch.object(permission_mgr, 'request_permission', return_value=True):
                result = tool.execute(command=f"rm {temp_path}")

                assert result["success"] == True
                assert result["returncode"] == 0

            # File should be deleted
            assert not os.path.exists(temp_path)
        finally:
            # Cleanup if test failed
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_bash_respects_timeout(self):
        """
        Test that BashTool respects timeout parameter.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        # Mock permission approval (sleep is risky)
        with patch.object(permission_mgr, 'request_permission', return_value=True):
            # Command that would run forever
            result = tool.execute(command="sleep 10", timeout=1)

            assert result["success"] == False
            assert "timeout" in result["error"].lower() or "timed out" in result["error"].lower()

    def test_bash_returns_stderr(self):
        """
        Test that BashTool returns stderr for failed commands.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        # Command that writes to stderr
        result = tool.execute(command="ls /nonexistent_directory_xyz")

        assert result["success"] == True  # Command executed, even if failed
        assert result["returncode"] != 0
        assert result["stderr"] != ""

    def test_bash_uses_working_directory(self):
        """
        Test that BashTool uses specified working directory.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager
        import tempfile

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool.execute(command="pwd", cwd=tmpdir)

            assert result["success"] == True
            assert tmpdir in result["stdout"]

    def test_bash_limits_output_size(self):
        """
        Test that BashTool limits output size to prevent memory issues.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        # Mock permission approval (seq might be risky)
        with patch.object(permission_mgr, 'request_permission', return_value=True):
            # Command that generates lots of output
            result = tool.execute(command="seq 1 100000")

            assert result["success"] == True
            # Output should be limited or truncated
            assert len(result["stdout"]) < 200000  # Less than 200KB


class TestBashToolIntegration:
    """Integration tests for BashTool."""

    def test_bash_tool_registers_in_registry(self):
        """
        Test that BashTool can be registered in ToolRegistry.

        This test should FAIL initially.
        """
        from tools.base import ToolRegistry
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        registry = ToolRegistry()
        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()

        registry.register(BashTool(sandbox, permission_mgr))

        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "bash"

    def test_bash_tool_schema_valid(self):
        """
        Test that BashTool generates valid function schema.

        This test should FAIL initially.
        """
        from tools.bash_tool import BashTool
        from safety.sandbox import CommandSandbox
        from safety.permissions import PermissionManager

        sandbox = CommandSandbox()
        permission_mgr = PermissionManager()
        tool = BashTool(sandbox, permission_mgr)

        schema = tool.to_function_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "bash"
        assert "command" in schema["function"]["parameters"]["properties"]
        assert "timeout" in schema["function"]["parameters"]["properties"]
