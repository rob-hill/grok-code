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
from typing import List, Dict, Any, Callable, Optional
from core.config import get_config


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

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
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
