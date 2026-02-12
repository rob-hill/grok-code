"""
Tests for file tools (Read, Glob, Grep).

Following TDD methodology.
"""
import pytest
import os
import tempfile
from pathlib import Path


class TestReadFileTool:
    """Test suite for ReadFileTool."""

    def test_read_file_tool_exists(self):
        """
        Test that ReadFileTool can be imported and instantiated.

        This test should FAIL initially.
        """
        from tools.file_tools import ReadFileTool

        tool = ReadFileTool()
        assert tool is not None
        assert tool.name == "read_file"

    def test_read_file_returns_contents(self):
        """
        Test that ReadFileTool reads and returns file contents.

        This test should FAIL initially.
        """
        from tools.file_tools import ReadFileTool

        # Create a temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            temp_path = f.name

        try:
            tool = ReadFileTool()
            result = tool.execute(file_path=temp_path)

            assert result["success"] == True
            assert "Line 1" in result["content"]
            assert "Line 2" in result["content"]
            assert "Line 3" in result["content"]
        finally:
            os.unlink(temp_path)

    def test_read_file_with_line_numbers(self):
        """
        Test that ReadFileTool returns content with line numbers (cat -n style).

        This test should FAIL initially.
        """
        from tools.file_tools import ReadFileTool

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("First line\nSecond line\nThird line\n")
            temp_path = f.name

        try:
            tool = ReadFileTool()
            result = tool.execute(file_path=temp_path)

            # Should have line numbers
            content = result["content"]
            assert "1→First line" in content or "1\tFirst line" in content or "  1" in content
        finally:
            os.unlink(temp_path)

    def test_read_file_handles_nonexistent(self):
        """
        Test that ReadFileTool handles nonexistent files gracefully.

        This test should FAIL initially.
        """
        from tools.file_tools import ReadFileTool

        tool = ReadFileTool()
        result = tool.execute(file_path="/nonexistent/file.txt")

        assert result["success"] == False
        assert "error" in result


class TestGlobTool:
    """Test suite for GlobTool."""

    def test_glob_tool_exists(self):
        """
        Test that GlobTool can be imported and instantiated.

        This test should FAIL initially.
        """
        from tools.file_tools import GlobTool

        tool = GlobTool()
        assert tool is not None
        assert tool.name == "glob"

    def test_glob_finds_files_by_pattern(self):
        """
        Test that GlobTool finds files matching pattern.

        This test should FAIL initially.
        """
        from tools.file_tools import GlobTool

        # Create temp directory with files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test1.py").write_text("python file 1")
            Path(tmpdir, "test2.py").write_text("python file 2")
            Path(tmpdir, "test.txt").write_text("text file")

            tool = GlobTool()
            result = tool.execute(pattern="*.py", path=tmpdir)

            assert result["success"] == True
            assert len(result["files"]) == 2
            assert any("test1.py" in f for f in result["files"])
            assert any("test2.py" in f for f in result["files"])

    def test_glob_recursive_pattern(self):
        """
        Test that GlobTool handles recursive patterns (**/).

        This test should FAIL initially.
        """
        from tools.file_tools import GlobTool

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(tmpdir, "root.py").write_text("root")
            Path(subdir, "nested.py").write_text("nested")

            tool = GlobTool()
            result = tool.execute(pattern="**/*.py", path=tmpdir)

            assert result["success"] == True
            assert len(result["files"]) == 2


class TestGrepTool:
    """Test suite for GrepTool."""

    def test_grep_tool_exists(self):
        """
        Test that GrepTool can be imported and instantiated.

        This test should FAIL initially.
        """
        from tools.file_tools import GrepTool

        tool = GrepTool()
        assert tool is not None
        assert tool.name == "grep"

    def test_grep_searches_file_content(self):
        """
        Test that GrepTool searches for patterns in files.

        This test should FAIL initially.
        """
        from tools.file_tools import GrepTool

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "file1.txt").write_text("Hello world\nPython is great\n")
            Path(tmpdir, "file2.txt").write_text("JavaScript is fun\nPython too\n")

            tool = GrepTool()
            result = tool.execute(
                pattern="Python",
                path=tmpdir,
                output_mode="files_with_matches"
            )

            assert result["success"] == True
            assert len(result["matches"]) == 2

    def test_grep_with_content_output(self):
        """
        Test that GrepTool can return matching lines with content.

        This test should FAIL initially.
        """
        from tools.file_tools import GrepTool

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("Line 1\nLine with ERROR\nLine 3\n")

            tool = GrepTool()
            result = tool.execute(
                pattern="ERROR",
                path=tmpdir,
                output_mode="content"
            )

            assert result["success"] == True
            assert "ERROR" in str(result["matches"])

    def test_grep_supports_regex(self):
        """
        Test that GrepTool supports regex patterns.

        This test should FAIL initially.
        """
        from tools.file_tools import GrepTool

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.py").write_text("def function1():\n    pass\n\ndef function2():\n    pass\n")

            tool = GrepTool()
            result = tool.execute(
                pattern=r"def\s+\w+",
                path=tmpdir,
                output_mode="content"
            )

            assert result["success"] == True
            # Should find both function definitions
            content_str = str(result["matches"])
            assert "function1" in content_str or "function2" in content_str


class TestFileToolsIntegration:
    """Integration tests for file tools."""

    def test_tools_register_in_registry(self):
        """
        Test that file tools can be registered in ToolRegistry.

        This test should FAIL initially.
        """
        from tools.base import ToolRegistry
        from tools.file_tools import ReadFileTool, GlobTool, GrepTool

        registry = ToolRegistry()
        registry.register(ReadFileTool())
        registry.register(GlobTool())
        registry.register(GrepTool())

        schemas = registry.get_schemas()
        assert len(schemas) == 3

        tool_names = [s["function"]["name"] for s in schemas]
        assert "read_file" in tool_names
        assert "glob" in tool_names
        assert "grep" in tool_names

    def test_read_file_schema_valid(self):
        """
        Test that ReadFileTool generates valid function schema.

        This test should FAIL initially.
        """
        from tools.file_tools import ReadFileTool

        tool = ReadFileTool()
        schema = tool.to_function_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "read_file"
        assert "file_path" in schema["function"]["parameters"]["properties"]
