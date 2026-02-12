"""
Base classes for tool system.

Provides Tool base class and ToolRegistry for managing tools.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class Tool(ABC):
    """
    Base class for all tools.

    Tools implement specific functionality (read files, execute commands, etc.)
    and expose themselves as functions to the AI model.
    """

    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        Initialize a tool.

        Args:
            name: Tool name (used in function calls)
            description: Human-readable description
            parameters: JSON schema for parameters
        """
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_function_schema(self) -> Dict[str, Any]:
        """
        Convert tool to xAI function calling schema.

        Returns:
            Function schema dict in xAI format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given arguments.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result dict
        """
        pass


class ToolRegistry:
    """
    Registry for managing available tools.

    Handles tool registration, schema generation, and execution.
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self.tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered. "
                "Tool names must be unique."
            )
        self.tools[tool.name] = tool

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        Get function schemas for all registered tools.

        Returns:
            List of function schema dicts
        """
        return [tool.to_function_schema() for tool in self.tools.values()]

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name.

        Args:
            name: Tool name to execute
            **kwargs: Arguments to pass to tool

        Returns:
            Tool execution result

        Raises:
            KeyError: If tool not found
        """
        if name not in self.tools:
            raise KeyError(
                f"Tool '{name}' not found in registry. "
                f"Available tools: {list(self.tools.keys())}"
            )

        tool = self.tools[name]
        return tool.execute(**kwargs)

    def get_tool(self, name: str) -> Tool:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance

        Raises:
            KeyError: If tool not found
        """
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self.tools[name]

    def __repr__(self):
        """String representation of registry."""
        tool_names = list(self.tools.keys())
        return f"ToolRegistry(tools={tool_names})"
