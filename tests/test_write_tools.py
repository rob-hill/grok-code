"""
Tests for write tools (Write, Edit) with safety integration.

Following TDD methodology - these tools MUST integrate with PathValidator and PermissionManager.
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestWriteFileTool:
    """Test suite for WriteFileTool with safety integration."""

    def test_write_file_tool_exists(self):
        """
        Test that WriteFileTool can be imported and instantiated.

        This test should FAIL initially.
        """
        from tools.file_tools import WriteFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        validator = PathValidator()
        permission_mgr = PermissionManager()
        tool = WriteFileTool(validator, permission_mgr)

        assert tool is not None
        assert tool.name == "write_file"

    def test_write_file_creates_new_file(self):
        """
        Test that WriteFileTool creates a new file.

        This test should FAIL initially.
        """
        from tools.file_tools import WriteFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "new_file.txt")
            content = "Hello, World!"

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = WriteFileTool(validator, permission_mgr)

            result = tool.execute(file_path=test_file, content=content)

            assert result["success"] == True
            assert os.path.exists(test_file)
            assert Path(test_file).read_text() == content

    def test_write_file_blocks_system_paths(self):
        """
        Test that WriteFileTool blocks writes to system directories.

        CRITICAL: Must use PathValidator to block dangerous paths.
        This test should FAIL initially.
        """
        from tools.file_tools import WriteFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        validator = PathValidator()
        permission_mgr = PermissionManager()
        tool = WriteFileTool(validator, permission_mgr)

        # Try to write to system directory
        result = tool.execute(
            file_path="/etc/dangerous_file.txt",
            content="malicious content"
        )

        assert result["success"] == False
        assert "denied" in result["error"].lower() or "blocked" in result["error"].lower()

    def test_write_file_requests_permission_for_overwrite(self):
        """
        Test that WriteFileTool requests permission when overwriting existing file.

        This test should FAIL initially.
        """
        from tools.file_tools import WriteFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "existing.txt")
            Path(test_file).write_text("original content")

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = WriteFileTool(validator, permission_mgr)

            # Mock user denying permission
            with patch.object(permission_mgr, 'request_permission', return_value=False):
                result = tool.execute(
                    file_path=test_file,
                    content="new content"
                )

                assert result["success"] == False
                assert "permission" in result["error"].lower() or "denied" in result["error"].lower()

            # File should still have original content
            assert Path(test_file).read_text() == "original content"

    def test_write_file_allows_overwrite_with_permission(self):
        """
        Test that WriteFileTool overwrites when permission granted.

        This test should FAIL initially.
        """
        from tools.file_tools import WriteFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "existing.txt")
            Path(test_file).write_text("original content")

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = WriteFileTool(validator, permission_mgr)

            # Mock user approving permission
            with patch.object(permission_mgr, 'request_permission', return_value=True):
                result = tool.execute(
                    file_path=test_file,
                    content="new content"
                )

                assert result["success"] == True

            # File should have new content
            assert Path(test_file).read_text() == "new content"

    def test_write_file_warns_about_sensitive_files(self):
        """
        Test that WriteFileTool warns when writing sensitive files.

        This test should FAIL initially.
        """
        from tools.file_tools import WriteFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sensitive_file = os.path.join(tmpdir, ".env")

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = WriteFileTool(validator, permission_mgr)

            # Mock permission approval
            with patch.object(permission_mgr, 'request_permission', return_value=True):
                result = tool.execute(
                    file_path=sensitive_file,
                    content="SECRET=value"
                )

                # Should succeed but with warning
                assert result["success"] == True
                if "warning" in result:
                    assert "sensitive" in result["warning"].lower()


class TestEditFileTool:
    """Test suite for EditFileTool with safety integration."""

    def test_edit_file_tool_exists(self):
        """
        Test that EditFileTool can be imported and instantiated.

        This test should FAIL initially.
        """
        from tools.file_tools import EditFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        validator = PathValidator()
        permission_mgr = PermissionManager()
        tool = EditFileTool(validator, permission_mgr)

        assert tool is not None
        assert tool.name == "edit_file"

    def test_edit_file_replaces_string(self):
        """
        Test that EditFileTool replaces exact string matches.

        This test should FAIL initially.
        """
        from tools.file_tools import EditFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            original = "def old_function():\n    pass\n"
            Path(test_file).write_text(original)

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = EditFileTool(validator, permission_mgr)

            # Mock permission approval
            with patch.object(permission_mgr, 'request_permission', return_value=True):
                result = tool.execute(
                    file_path=test_file,
                    old_string="old_function",
                    new_string="new_function"
                )

                assert result["success"] == True

            # Check file was edited
            content = Path(test_file).read_text()
            assert "new_function" in content
            assert "old_function" not in content

    def test_edit_file_blocks_system_paths(self):
        """
        Test that EditFileTool blocks edits to system files.

        CRITICAL: Must use PathValidator.
        This test should FAIL initially.
        """
        from tools.file_tools import EditFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        validator = PathValidator()
        permission_mgr = PermissionManager()
        tool = EditFileTool(validator, permission_mgr)

        result = tool.execute(
            file_path="/etc/passwd",
            old_string="root",
            new_string="hacker"
        )

        assert result["success"] == False
        assert "denied" in result["error"].lower() or "blocked" in result["error"].lower()

    def test_edit_file_requests_permission(self):
        """
        Test that EditFileTool always requests permission (risky operation).

        This test should FAIL initially.
        """
        from tools.file_tools import EditFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).write_text("original text")

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = EditFileTool(validator, permission_mgr)

            # Mock user denying permission
            with patch.object(permission_mgr, 'request_permission', return_value=False):
                result = tool.execute(
                    file_path=test_file,
                    old_string="original",
                    new_string="modified"
                )

                assert result["success"] == False

            # File should be unchanged
            assert Path(test_file).read_text() == "original text"

    def test_edit_file_replace_all_flag(self):
        """
        Test that EditFileTool can replace all occurrences with replace_all flag.

        This test should FAIL initially.
        """
        from tools.file_tools import EditFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            original = "foo bar foo baz foo"
            Path(test_file).write_text(original)

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = EditFileTool(validator, permission_mgr)

            # Mock permission approval
            with patch.object(permission_mgr, 'request_permission', return_value=True):
                result = tool.execute(
                    file_path=test_file,
                    old_string="foo",
                    new_string="FOO",
                    replace_all=True
                )

                assert result["success"] == True

            # All occurrences should be replaced
            content = Path(test_file).read_text()
            assert content == "FOO bar FOO baz FOO"

    def test_edit_file_handles_nonexistent_file(self):
        """
        Test that EditFileTool handles nonexistent files gracefully.

        This test should FAIL initially.
        """
        from tools.file_tools import EditFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        validator = PathValidator()
        permission_mgr = PermissionManager()
        tool = EditFileTool(validator, permission_mgr)

        result = tool.execute(
            file_path="/nonexistent/file.txt",
            old_string="old",
            new_string="new"
        )

        assert result["success"] == False
        assert "not found" in result["error"].lower() or "exist" in result["error"].lower()

    def test_edit_file_fails_if_old_string_not_found(self):
        """
        Test that EditFileTool fails if old_string not found in file.

        This test should FAIL initially.
        """
        from tools.file_tools import EditFileTool
        from safety.validators import PathValidator
        from safety.permissions import PermissionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).write_text("some content")

            validator = PathValidator()
            permission_mgr = PermissionManager()
            tool = EditFileTool(validator, permission_mgr)

            # Mock permission approval
            with patch.object(permission_mgr, 'request_permission', return_value=True):
                result = tool.execute(
                    file_path=test_file,
                    old_string="nonexistent string",
                    new_string="new"
                )

                assert result["success"] == False
                assert "not found" in result["error"].lower()
