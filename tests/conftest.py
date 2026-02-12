"""
Pytest configuration and fixtures for grok-code tests.
"""
import pytest
import os
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("XAI_API_KEY", "test-api-key")
    monkeypatch.setenv("XAI_CHAT_ENDPOINT", "https://api.x.ai/v1/chat/completions")
    monkeypatch.setenv("XAI_MODEL", "grok-code-fast-1")
    monkeypatch.setenv("XAI_TEMPERATURE", "0.7")
    monkeypatch.setenv("GROK_CODE_WORKING_DIR", "/test/working/dir")
    monkeypatch.setenv("GROK_CODE_MAX_TOOL_ITERATIONS", "10")


@pytest.fixture
def sample_messages():
    """Sample conversation messages."""
    return [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Read the file test.py"}
    ]


@pytest.fixture
def sample_tools():
    """Sample tool schemas."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    ]


@pytest.fixture
def mock_api_response_no_tools():
    """Mock API response without tool calls."""
    return {
        "id": "test-id",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "grok-code-fast-1",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Here is the file contents..."
                },
                "finish_reason": "stop"
            }
        ]
    }


@pytest.fixture
def mock_api_response_with_tool_call():
    """Mock API response with tool call."""
    return {
        "id": "test-id",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "grok-code-fast-1",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "read_file",
                                "arguments": '{"file_path": "/test/file.py"}'
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ]
    }
