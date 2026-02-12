"""
Tests for tools.base module (Tool Registry System).

Following TDD methodology:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve code quality
"""
import pytest
from unittest.mock import Mock


class TestToolBase:
    """Test suite for Tool base class."""

    def test_tool_can_be_created(self):
        """
        Test that a Tool can be instantiated.

        This test should FAIL initially because tools.base doesn't exist yet.
        """
        from tools.base import Tool

        class TestTool(Tool):
            def __init__(self):
                super().__init__(
                    name="test_tool",
                    description="A test tool",
                    parameters={
                        "type": "object",
                        "properties": {
                            "arg1": {"type": "string", "description": "First argument"}
                        },
                        "required": ["arg1"]
                    }
                )

            def execute(self, **kwargs):
                return {"result": f"Executed with {kwargs}"}

        tool = TestTool()
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert "properties" in tool.parameters

    def test_tool_generates_function_schema(self):
        """
        Test that Tool can generate xAI function calling schema.

        This test should FAIL initially.
        """
        from tools.base import Tool

        class TestTool(Tool):
            def __init__(self):
                super().__init__(
                    name="read_file",
                    description="Read contents of a file",
                    parameters={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file"
                            }
                        },
                        "required": ["file_path"]
                    }
                )

            def execute(self, **kwargs):
                return {"content": "file contents"}

        tool = TestTool()
        schema = tool.to_function_schema()

        # Verify schema format matches xAI expectations
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "read_file"
        assert schema["function"]["description"] == "Read contents of a file"
        assert schema["function"]["parameters"]["type"] == "object"
        assert "file_path" in schema["function"]["parameters"]["properties"]

    def test_tool_can_be_executed(self):
        """
        Test that Tool can be executed with arguments.

        This test should FAIL initially.
        """
        from tools.base import Tool

        class TestTool(Tool):
            def __init__(self):
                super().__init__(
                    name="test_tool",
                    description="A test tool",
                    parameters={"type": "object", "properties": {}}
                )

            def execute(self, **kwargs):
                return {"result": "success", "args": kwargs}

        tool = TestTool()
        result = tool.execute(arg1="value1", arg2="value2")

        assert result["result"] == "success"
        assert result["args"]["arg1"] == "value1"
        assert result["args"]["arg2"] == "value2"


class TestToolRegistry:
    """Test suite for ToolRegistry."""

    def test_registry_can_register_tool(self):
        """
        Test that tools can be registered in the registry.

        This test should FAIL initially.
        """
        from tools.base import Tool, ToolRegistry

        class TestTool(Tool):
            def __init__(self):
                super().__init__(
                    name="test_tool",
                    description="A test tool",
                    parameters={"type": "object", "properties": {}}
                )

            def execute(self, **kwargs):
                return {"result": "success"}

        registry = ToolRegistry()
        tool = TestTool()
        registry.register(tool)

        # Verify tool is registered
        assert "test_tool" in registry.tools
        assert registry.tools["test_tool"] == tool

    def test_registry_can_get_all_schemas(self):
        """
        Test that registry can return all tool schemas.

        This test should FAIL initially.
        """
        from tools.base import Tool, ToolRegistry

        class Tool1(Tool):
            def __init__(self):
                super().__init__(
                    name="tool1",
                    description="First tool",
                    parameters={"type": "object", "properties": {}}
                )

            def execute(self, **kwargs):
                return {}

        class Tool2(Tool):
            def __init__(self):
                super().__init__(
                    name="tool2",
                    description="Second tool",
                    parameters={"type": "object", "properties": {}}
                )

            def execute(self, **kwargs):
                return {}

        registry = ToolRegistry()
        registry.register(Tool1())
        registry.register(Tool2())

        schemas = registry.get_schemas()

        # Verify schemas
        assert len(schemas) == 2
        assert all(schema["type"] == "function" for schema in schemas)
        tool_names = [schema["function"]["name"] for schema in schemas]
        assert "tool1" in tool_names
        assert "tool2" in tool_names

    def test_registry_can_execute_tool_by_name(self):
        """
        Test that registry can execute a tool by name with arguments.

        This test should FAIL initially.
        """
        from tools.base import Tool, ToolRegistry

        class TestTool(Tool):
            def __init__(self):
                super().__init__(
                    name="test_tool",
                    description="A test tool",
                    parameters={"type": "object", "properties": {}}
                )

            def execute(self, **kwargs):
                return {"result": "executed", "args": kwargs}

        registry = ToolRegistry()
        registry.register(TestTool())

        # Execute tool by name
        result = registry.execute("test_tool", arg1="value1", arg2="value2")

        assert result["result"] == "executed"
        assert result["args"]["arg1"] == "value1"
        assert result["args"]["arg2"] == "value2"

    def test_registry_raises_error_for_unknown_tool(self):
        """
        Test that registry raises error for unknown tool.

        This test should FAIL initially.
        """
        from tools.base import ToolRegistry

        registry = ToolRegistry()

        with pytest.raises(KeyError, match="unknown_tool"):
            registry.execute("unknown_tool")

    def test_registry_prevents_duplicate_tool_names(self):
        """
        Test that registry prevents registering duplicate tool names.

        This test should FAIL initially.
        """
        from tools.base import Tool, ToolRegistry

        class TestTool1(Tool):
            def __init__(self):
                super().__init__(
                    name="duplicate_name",
                    description="First tool",
                    parameters={"type": "object", "properties": {}}
                )

            def execute(self, **kwargs):
                return {}

        class TestTool2(Tool):
            def __init__(self):
                super().__init__(
                    name="duplicate_name",
                    description="Second tool",
                    parameters={"type": "object", "properties": {}}
                )

            def execute(self, **kwargs):
                return {}

        registry = ToolRegistry()
        registry.register(TestTool1())

        # Should raise error on duplicate name
        with pytest.raises(ValueError, match="already registered"):
            registry.register(TestTool2())
