"""
File manipulation tools for grok-code.

Implements Read, Glob, Grep, Write, and Edit tools.
"""
import os
import glob as glob_module
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from tools.base import Tool
from safety.validators import PathValidator
from safety.permissions import PermissionManager


class ReadFileTool(Tool):
    """
    Read contents of a file with line numbers.

    Safe operation - no permission needed.
    """

    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read contents of a file from the filesystem",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to read"
                    },
                    "offset": {
                        "type": "number",
                        "description": "Line number to start reading from (optional, 1-indexed)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of lines to read (optional, default: all)"
                    }
                },
                "required": ["file_path"]
            }
        )

    def execute(
        self,
        file_path: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute file read.

        Args:
            file_path: Path to file
            offset: Start line (1-indexed)
            limit: Number of lines to read

        Returns:
            Dict with success, content (with line numbers), path
        """
        try:
            # Expand path
            abs_path = os.path.abspath(os.path.expanduser(file_path))

            # Check if file exists
            if not os.path.exists(abs_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            # Check if it's a file (not directory)
            if not os.path.isfile(abs_path):
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}"
                }

            # Read file
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            # Apply offset and limit
            start = (offset - 1) if offset else 0
            end = (start + limit) if limit else len(lines)
            lines = lines[start:end]

            # Format with line numbers (cat -n style)
            formatted_lines = []
            for i, line in enumerate(lines, start=start + 1):
                # Remove trailing newline for formatting
                line_content = line.rstrip('\n')
                formatted_lines.append(f"{i:6d}→{line_content}")

            content = '\n'.join(formatted_lines)

            return {
                "success": True,
                "content": content,
                "path": abs_path,
                "lines_read": len(lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}"
            }


class GlobTool(Tool):
    """
    Find files by pattern (e.g., "**/*.py", "src/**/*.ts").

    Safe operation - no permission needed.
    """

    def __init__(self):
        super().__init__(
            name="glob",
            description="Find files matching a glob pattern",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '*.py', '**/*.ts')"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (optional, default: current directory)"
                    }
                },
                "required": ["pattern"]
            }
        )

    def execute(
        self,
        pattern: str,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute file search by pattern.

        Args:
            pattern: Glob pattern
            path: Directory to search in

        Returns:
            Dict with success, files list, pattern
        """
        try:
            # Set search directory
            search_dir = path if path else os.getcwd()
            search_dir = os.path.abspath(os.path.expanduser(search_dir))

            # Combine path and pattern
            search_pattern = os.path.join(search_dir, pattern)

            # Find files
            files = glob_module.glob(search_pattern, recursive=True)

            # Sort by modification time (most recent first)
            files.sort(key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0, reverse=True)

            return {
                "success": True,
                "files": files,
                "pattern": pattern,
                "count": len(files)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching files: {str(e)}"
            }


class GrepTool(Tool):
    """
    Search file contents with regex.

    Safe operation - no permission needed.
    """

    def __init__(self):
        super().__init__(
            name="grep",
            description="Search file contents using regex patterns",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "File or directory to search in (optional, default: current directory)"
                    },
                    "output_mode": {
                        "type": "string",
                        "description": "Output mode: 'content' (show lines), 'files_with_matches' (show file paths), or 'count' (show counts)",
                        "enum": ["content", "files_with_matches", "count"]
                    },
                    "case_insensitive": {
                        "type": "boolean",
                        "description": "Case insensitive search (optional, default: false)"
                    }
                },
                "required": ["pattern"]
            }
        )

    def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        output_mode: str = "files_with_matches",
        case_insensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Execute content search.

        Args:
            pattern: Regex pattern
            path: File or directory to search
            output_mode: How to format results
            case_insensitive: Case insensitive search

        Returns:
            Dict with success, matches (format depends on output_mode)
        """
        try:
            # Set search path
            search_path = path if path else os.getcwd()
            search_path = os.path.abspath(os.path.expanduser(search_path))

            # Compile regex
            flags = re.IGNORECASE if case_insensitive else 0
            regex = re.compile(pattern, flags)

            # Collect files to search
            if os.path.isfile(search_path):
                files = [search_path]
            else:
                # Search all files in directory
                files = []
                for root, dirs, filenames in os.walk(search_path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))

            # Search files
            matches = []
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        if output_mode == "content":
                            # Show matching lines
                            for line_num, line in enumerate(f, 1):
                                if regex.search(line):
                                    matches.append({
                                        "file": file_path,
                                        "line": line_num,
                                        "content": line.rstrip('\n')
                                    })
                        elif output_mode == "count":
                            # Count matches
                            count = sum(1 for line in f if regex.search(line))
                            if count > 0:
                                matches.append({
                                    "file": file_path,
                                    "count": count
                                })
                        else:  # files_with_matches
                            # Just file paths with matches
                            content = f.read()
                            if regex.search(content):
                                matches.append(file_path)
                except Exception:
                    # Skip files that can't be read
                    continue

            return {
                "success": True,
                "matches": matches,
                "pattern": pattern,
                "output_mode": output_mode
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error searching content: {str(e)}"
            }


class WriteFileTool(Tool):
    """
    Write or create a file.

    REQUIRES: PathValidator and PermissionManager for safety.
    """

    def __init__(self, path_validator: PathValidator, permission_manager: PermissionManager):
        """
        Initialize WriteFileTool with safety components.

        Args:
            path_validator: PathValidator instance
            permission_manager: PermissionManager instance
        """
        super().__init__(
            name="write_file",
            description="Create a new file or overwrite an existing file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        )
        self.path_validator = path_validator
        self.permission_manager = permission_manager

    def execute(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Execute file write.

        Args:
            file_path: Path to file
            content: Content to write

        Returns:
            Dict with success, path, and optional warning
        """
        try:
            # Expand path
            abs_path = os.path.abspath(os.path.expanduser(file_path))

            # Validate path safety
            is_valid, warning = self.path_validator.validate_path(abs_path, "write")
            if not is_valid:
                return {
                    "success": False,
                    "error": warning
                }

            # Check if file exists (overwrite scenario)
            file_exists = os.path.exists(abs_path)

            # Request permission if overwriting or if there's a warning
            if file_exists or warning:
                details = {
                    "path": abs_path,
                    "operation": "overwrite" if file_exists else "create",
                    "risk": "medium" if file_exists else "low"
                }
                if warning:
                    details["warning"] = warning

                approved = self.permission_manager.request_permission(
                    operation="write_file",
                    details=details
                )

                if not approved:
                    return {
                        "success": False,
                        "error": "Permission denied by user"
                    }

            # Create directory if needed
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # Write file
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result = {
                "success": True,
                "path": abs_path,
                "bytes_written": len(content.encode('utf-8'))
            }

            if warning:
                result["warning"] = warning

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}"
            }


class EditFileTool(Tool):
    """
    Edit an existing file with exact string replacement.

    REQUIRES: PathValidator and PermissionManager for safety.
    """

    def __init__(self, path_validator: PathValidator, permission_manager: PermissionManager):
        """
        Initialize EditFileTool with safety components.

        Args:
            path_validator: PathValidator instance
            permission_manager: PermissionManager instance
        """
        super().__init__(
            name="edit_file",
            description="Edit an existing file by replacing exact string matches",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file"
                    },
                    "old_string": {
                        "type": "string",
                        "description": "Exact string to replace"
                    },
                    "new_string": {
                        "type": "string",
                        "description": "String to replace with"
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace all occurrences (default: false, only first)"
                    }
                },
                "required": ["file_path", "old_string", "new_string"]
            }
        )
        self.path_validator = path_validator
        self.permission_manager = permission_manager

    def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False
    ) -> Dict[str, Any]:
        """
        Execute file edit.

        Args:
            file_path: Path to file
            old_string: String to replace
            new_string: Replacement string
            replace_all: Replace all occurrences

        Returns:
            Dict with success, path, replacements count
        """
        try:
            # Expand path
            abs_path = os.path.abspath(os.path.expanduser(file_path))

            # Check if file exists
            if not os.path.exists(abs_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            # Validate path safety
            is_valid, warning = self.path_validator.validate_path(abs_path, "write")
            if not is_valid:
                return {
                    "success": False,
                    "error": warning
                }

            # Request permission (editing is always risky)
            details = {
                "path": abs_path,
                "operation": "edit",
                "old_string": old_string[:50] + "..." if len(old_string) > 50 else old_string,
                "new_string": new_string[:50] + "..." if len(new_string) > 50 else new_string,
                "risk": "medium"
            }
            if warning:
                details["warning"] = warning

            approved = self.permission_manager.request_permission(
                operation="edit_file",
                details=details
            )

            if not approved:
                return {
                    "success": False,
                    "error": "Permission denied by user"
                }

            # Read file
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if old_string exists
            if old_string not in content:
                return {
                    "success": False,
                    "error": f"String not found in file: '{old_string[:50]}...'"
                }

            # Replace string
            if replace_all:
                new_content = content.replace(old_string, new_string)
                count = content.count(old_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
                count = 1

            # Write back
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            result = {
                "success": True,
                "path": abs_path,
                "replacements": count
            }

            if warning:
                result["warning"] = warning

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Error editing file: {str(e)}"
            }
