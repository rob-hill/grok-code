#!/usr/bin/env python3
"""
grok-code: Terminal-based coding agent powered by Grok/XAI.

A Claude Code-like experience using Grok's powerful reasoning capabilities.
"""
import sys
import os
import argparse
from rich.console import Console
from rich.markdown import Markdown

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api_client import execute_with_tools, execute_simple
from core.config import get_config
from tools.base import ToolRegistry
from tools.file_tools import ReadFileTool, GlobTool, GrepTool, WriteFileTool, EditFileTool
from tools.bash_tool import BashTool
from safety.validators import PathValidator
from safety.sandbox import CommandSandbox
from safety.permissions import PermissionManager


def create_system_prompt() -> str:
    """Create system prompt for grok-code."""
    config = get_config()
    return f"""You are grok-code, a terminal-based coding agent powered by Grok/XAI.

Your role is to help users with software engineering tasks using the tools available to you.

AVAILABLE TOOLS:
- read_file: Read contents of files
- glob: Find files by pattern (e.g., "**/*.py")
- grep: Search file contents with regex
- write_file: Create or overwrite files (requires permission)
- edit_file: Edit files with exact string replacement (requires permission)
- bash: Execute bash commands (safe commands auto-approved, risky require permission)

SAFETY FEATURES:
- System directories (/etc, /usr, /bin, etc.) are protected
- Destructive commands (rm -rf, dd, mkfs) are blocked
- Risky operations require user approval
- All file modifications are validated

WORKING DIRECTORY: {config.working_dir}

GUIDELINES:
- Always use absolute or relative paths for file operations
- Explore the codebase using read_file, glob, and grep before making changes
- Request permission clearly for risky operations
- Execute commands safely and report results clearly
- Be concise and helpful
"""


def setup_tools() -> ToolRegistry:
    """Initialize and register all tools."""
    registry = ToolRegistry()

    # Safety components
    path_validator = PathValidator()
    command_sandbox = CommandSandbox()
    permission_manager = PermissionManager()

    # Register read-only tools (no permissions needed)
    registry.register(ReadFileTool())
    registry.register(GlobTool())
    registry.register(GrepTool())

    # Register write tools (with safety)
    registry.register(WriteFileTool(path_validator, permission_manager))
    registry.register(EditFileTool(path_validator, permission_manager))

    # Register bash tool (with sandboxing)
    registry.register(BashTool(command_sandbox, permission_manager))

    return registry


def tool_executor(tool_registry: ToolRegistry):
    """Create tool executor function for API client."""
    def execute(name: str, args: dict):
        """Execute a tool by name with arguments."""
        return tool_registry.execute(name, **args)
    return execute


def main():
    """Main entry point for grok-code."""
    parser = argparse.ArgumentParser(
        description="grok-code - Terminal coding agent powered by Grok/XAI"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to execute (interactive mode if not provided)"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Force interactive mode"
    )

    args = parser.parse_args()

    # Initialize console
    console = Console()

    try:
        # Setup
        config = get_config()
        tool_registry = setup_tools()
        system_prompt = create_system_prompt()

        console.print(f"\n[bold cyan]grok-code[/bold cyan] - Powered by {config.model}")
        console.print(f"Working directory: {config.working_dir}\n")

        if args.query and not args.interactive:
            # Single query mode
            console.print(f"[bold]User:[/bold] {args.query}\n")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": args.query}
            ]

            with console.status("[bold green]Thinking..."):
                result = execute_with_tools(
                    messages=messages,
                    tools=tool_registry.get_schemas(),
                    tool_executor=tool_executor(tool_registry),
                    max_iterations=config.max_tool_iterations
                )

            console.print(f"\n[bold]grok-code:[/bold]")
            console.print(Markdown(result))

        else:
            # Interactive mode
            console.print("[dim]Type your query or /exit to quit[/dim]\n")

            messages = [{"role": "system", "content": system_prompt}]

            while True:
                try:
                    user_input = input("\n[bold cyan]You:[/bold cyan] ").strip()

                    if not user_input:
                        continue

                    if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                        console.print("\n[dim]Goodbye![/dim]")
                        break

                    if user_input == "/clear":
                        messages = [{"role": "system", "content": system_prompt}]
                        console.print("[dim]Conversation cleared[/dim]")
                        continue

                    if user_input == "/tools":
                        console.print("\n[bold]Available tools:[/bold]")
                        for schema in tool_registry.get_schemas():
                            name = schema["function"]["name"]
                            desc = schema["function"]["description"]
                            console.print(f"  • {name}: {desc}")
                        continue

                    # Add user message
                    messages.append({"role": "user", "content": user_input})

                    # Execute with tools
                    with console.status("[bold green]Thinking..."):
                        result = execute_with_tools(
                            messages=messages,
                            tools=tool_registry.get_schemas(),
                            tool_executor=tool_executor(tool_registry),
                            max_iterations=config.max_tool_iterations
                        )

                    # Display result
                    console.print(f"\n[bold]grok-code:[/bold]")
                    console.print(Markdown(result))

                    # Add assistant response to conversation
                    messages.append({"role": "assistant", "content": result})

                except KeyboardInterrupt:
                    console.print("\n\n[dim]Use /exit to quit[/dim]")
                    continue
                except EOFError:
                    console.print("\n[dim]Goodbye![/dim]")
                    break

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        import traceback
        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
