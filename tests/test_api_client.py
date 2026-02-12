"""
Tests for core.api_client module.

Following TDD methodology:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve code quality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestAPIClient:
    """Test suite for API client functionality."""

    def test_api_client_can_call_xai(self, mock_env_vars, sample_messages, mock_api_response_no_tools):
        """
        Test basic API connectivity to /v1/chat/completions.

        This test should FAIL initially because core.api_client doesn't exist yet.
        """
        from core.api_client import call_api

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_api_response_no_tools
            mock_post.return_value.status_code = 200

            response = call_api(sample_messages, [])

            # Verify API was called correctly
            assert mock_post.called
            call_args = mock_post.call_args

            # Check endpoint
            assert call_args[0][0] == "https://api.x.ai/v1/chat/completions"

            # Check headers include Bearer token
            assert "Authorization" in call_args[1]["headers"]
            assert call_args[1]["headers"]["Authorization"] == "Bearer test-api-key"

            # Check request body
            request_body = call_args[1]["json"]
            assert request_body["model"] == "grok-code-fast-1"
            assert request_body["messages"] == sample_messages

            # Check response
            assert response is not None
            assert response["choices"][0]["message"]["content"] == "Here is the file contents..."

    def test_api_client_extracts_tool_calls(self, mock_env_vars, sample_messages, mock_api_response_with_tool_call):
        """
        Test that API client can extract tool calls from response.

        This test should FAIL initially.
        """
        from core.api_client import call_api

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_api_response_with_tool_call
            mock_post.return_value.status_code = 200

            response = call_api(sample_messages, [])

            # Verify response contains tool calls
            assert "tool_calls" in response["choices"][0]["message"]
            tool_calls = response["choices"][0]["message"]["tool_calls"]
            assert len(tool_calls) == 1
            assert tool_calls[0]["function"]["name"] == "read_file"

    def test_api_client_handles_tool_execution_loop(self, mock_env_vars, sample_messages, sample_tools):
        """
        Test function calling loop: API call → execute tool → send results → repeat.

        This test should FAIL initially.
        """
        from core.api_client import execute_with_tools

        # Mock API responses: first with tool call, second with final answer
        first_response = {
            "id": "test-id-1",
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

        second_response = {
            "id": "test-id-2",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "grok-code-fast-1",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "The file contains: print('hello')"
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        # Mock tool executor
        mock_tool_executor = Mock(return_value={"content": "print('hello')", "success": True})

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            # First call returns tool_calls, second call returns final answer
            mock_post.return_value.json.side_effect = [first_response, second_response]

            result = execute_with_tools(
                messages=sample_messages,
                tools=sample_tools,
                tool_executor=mock_tool_executor,
                max_iterations=10
            )

            # Verify tool was executed
            assert mock_tool_executor.called
            call_args = mock_tool_executor.call_args
            assert call_args[0][0] == "read_file"  # tool name
            assert call_args[0][1] == {"file_path": "/test/file.py"}  # arguments

            # Verify API was called twice (once for tool call, once after tool result)
            assert mock_post.call_count == 2

            # Verify final result
            assert result is not None
            assert "The file contains" in result

    def test_api_client_respects_max_iterations(self, mock_env_vars, sample_messages, sample_tools):
        """
        Test that tool loop stops after max_iterations to prevent infinite loops.

        This test should FAIL initially.
        """
        from core.api_client import execute_with_tools

        # Mock API to always return tool calls (infinite loop scenario)
        infinite_tool_response = {
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

        mock_tool_executor = Mock(return_value={"content": "test"})

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = infinite_tool_response

            # Should stop after max_iterations
            with pytest.raises(Exception, match="Maximum tool iterations reached"):
                execute_with_tools(
                    messages=sample_messages,
                    tools=sample_tools,
                    tool_executor=mock_tool_executor,
                    max_iterations=3
                )

            # Verify it stopped at max_iterations (3 calls)
            assert mock_post.call_count == 3

    def test_api_client_handles_errors(self, mock_env_vars, sample_messages):
        """
        Test error handling for failed API calls.

        This test should FAIL initially.
        """
        from core.api_client import call_api

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = "Internal Server Error"

            with pytest.raises(Exception, match="API request failed"):
                call_api(sample_messages, [])


class TestConfig:
    """Test suite for configuration management."""

    def test_config_loads_from_env(self, mock_env_vars):
        """
        Test that configuration loads from environment variables.

        This test should FAIL initially because core.config doesn't exist yet.
        """
        from core.config import Config

        config = Config()

        assert config.api_key == "test-api-key"
        assert config.chat_endpoint == "https://api.x.ai/v1/chat/completions"
        assert config.model == "grok-code-fast-1"
        assert config.temperature == 0.7
        assert config.working_dir == "/test/working/dir"
        assert config.max_tool_iterations == 10

    def test_config_validates_required_settings(self, monkeypatch):
        """
        Test that configuration validates required settings.

        This test should FAIL initially.
        """
        from unittest.mock import patch

        # Mock load_dotenv to not load from .env file
        with patch('core.config.load_dotenv'):
            # Remove required API key
            monkeypatch.delenv("XAI_API_KEY", raising=False)

            from core.config import Config

            with pytest.raises(ValueError, match="XAI_API_KEY"):
                Config()

    def test_config_provides_defaults(self, monkeypatch):
        """
        Test that configuration provides sensible defaults.

        This test should FAIL initially.
        """
        from core.config import Config

        # Set only required env vars
        monkeypatch.setenv("XAI_API_KEY", "test-key")

        config = Config()

        # Should have defaults
        assert config.model == "grok-code-fast-1"
        assert config.temperature == 0.7
        assert config.max_tool_iterations == 20
