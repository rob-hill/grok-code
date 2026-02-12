"""
Configuration management for grok-code.

Loads configuration from environment variables with sensible defaults.
"""
import os
from dotenv import load_dotenv


class Config:
    """Configuration loaded from environment variables."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file
        load_dotenv()

        # Required settings
        self.api_key = os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable is required")

        # API configuration
        self.chat_endpoint = os.getenv(
            "XAI_CHAT_ENDPOINT",
            "https://api.x.ai/v1/chat/completions"
        )
        self.model = os.getenv("XAI_MODEL", "grok-code-fast-1")
        self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.7"))

        # grok-code specific settings
        self.working_dir = os.getenv(
            "GROK_CODE_WORKING_DIR",
            os.getcwd()
        )
        self.max_tool_iterations = int(os.getenv("GROK_CODE_MAX_TOOL_ITERATIONS", "20"))

    def __repr__(self):
        """String representation of config (hiding API key)."""
        return (
            f"Config(model={self.model}, "
            f"temperature={self.temperature}, "
            f"max_iterations={self.max_tool_iterations})"
        )


# Global configuration instance
_config = None


def get_config():
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
