"""
xAI API client with function calling support.

Implements the tool execution loop:
1. Call API with messages and tools
2. If response contains tool_calls, execute them
3. Send tool results back to API
4. Repeat until final answer or max iterations
"""
import requests
import json
import time
from typing import List, Dict, Any, Callable, Optional
from core.config import get_config


class RateLimiter:
    """
    Simple rate limiter to prevent API abuse and cost overruns.

    Tracks API calls and enforces limits.
    """

    def __init__(self, max_calls_per_minute: int = 60, max_calls_per_session: int = 200):
        """
        Initialize rate limiter.

        Args:
            max_calls_per_minute: Maximum API calls per minute
            max_calls_per_session: Maximum total API calls per session
        """
        self.max_calls_per_minute = max_calls_per_minute
        self.max_calls_per_session = max_calls_per_session
        self.call_times = []
        self.total_calls = 0

    def check_and_wait(self) -> None:
        """
        Check rate limits and wait if necessary.

        Raises:
            Exception: If session limit exceeded
        """
        now = time.time()

        # Check session limit
        if self.total_calls >= self.max_calls_per_session:
            raise Exception(
                f"Session API call limit reached ({self.max_calls_per_session} calls). "
                "This prevents cost overruns. Restart to reset."
            )

        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if now - t < 60]

        # Check per-minute limit
        if len(self.call_times) >= self.max_calls_per_minute:
            # Calculate wait time
            oldest_call = self.call_times[0]
            wait_time = 60 - (now - oldest_call)
            if wait_time > 0:
                print(f"⏱️  Rate limit: Waiting {wait_time:.1f}s before next API call...")
                time.sleep(wait_time)
                now = time.time()

        # Record this call
        self.call_times.append(now)
        self.total_calls += 1

    def get_stats(self) -> Dict[str, int]:
        """Get rate limiter statistics."""
        now = time.time()
        recent_calls = len([t for t in self.call_times if now - t < 60])
        return {
            "total_calls": self.total_calls,
            "calls_last_minute": recent_calls,
            "remaining_session_calls": self.max_calls_per_session - self.total_calls
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


def call_api(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Call xAI Chat Completions API.

    Args:
        messages: Conversation messages
        tools: Available tool schemas

    Returns:
        API response dict

    Raises:
        Exception: If API request fails
    """
    config = get_config()

    # SECURITY: Check rate limits before making API call
    _rate_limiter.check_and_wait()

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        # SECURITY: Add security headers
        "User-Agent": "grok-code/1.0",
        "X-Client-Version": "1.0.0"
    }

    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature
    }

    # Only include tools if provided
    if tools:
        payload["tools"] = tools

    response = requests.post(
        config.chat_endpoint,
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(
            f"API request failed with status {response.status_code}: {response.text}"
        )

    return response.json()


def execute_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    tool_executor: Callable[[str, Dict[str, Any]], Dict[str, Any]],
    max_iterations: int = 20
) -> str:
    """
    Execute conversation with tool calling loop.

    Args:
        messages: Initial conversation messages
        tools: Available tool schemas
        tool_executor: Function to execute tools (name, args) -> result
        max_iterations: Maximum number of iterations to prevent infinite loops

    Returns:
        Final assistant response text

    Raises:
        Exception: If max iterations reached or API fails
    """
    conversation = messages.copy()
    iterations = 0

    while iterations < max_iterations:
        iterations += 1

        # Call API
        response = call_api(conversation, tools)

        # Extract assistant message
        assistant_message = response["choices"][0]["message"]
        finish_reason = response["choices"][0]["finish_reason"]

        # Add assistant message to conversation
        conversation.append(assistant_message)

        # Check if we're done
        if finish_reason == "stop":
            return assistant_message.get("content", "")

        # Handle tool calls
        if finish_reason == "tool_calls" and "tool_calls" in assistant_message:
            tool_calls = assistant_message["tool_calls"]

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])

                # Execute tool
                tool_result = tool_executor(tool_name, tool_args)

                # Add tool result to conversation
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result)
                }
                conversation.append(tool_message)

            # Continue loop to send tool results back
            continue

        # Unknown finish reason
        return assistant_message.get("content", "")

    # Max iterations reached
    raise Exception(
        f"Maximum tool iterations reached ({max_iterations}). "
        "The model may be stuck in a loop."
    )


def execute_simple(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Execute a simple API call without tool execution.

    Args:
        messages: Conversation messages
        tools: Optional tool schemas (won't be executed)

    Returns:
        Assistant response text
    """
    response = call_api(messages, tools or [])
    return response["choices"][0]["message"].get("content", "")
