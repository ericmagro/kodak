"""Shared Anthropic client for Kodak.

All LLM calls should go through this module.
Provides a single client instance with consistent timeout and error handling.
"""

import logging
import anthropic
from typing import Optional

logger = logging.getLogger('kodak')

# Default timeout for all LLM calls (seconds)
DEFAULT_TIMEOUT = 30.0

# Default model
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Singleton client
_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    """Get the shared Anthropic client. Lazy-loaded on first call."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            timeout=DEFAULT_TIMEOUT
        )
        logger.info("Anthropic client initialized")
    return _client


def create_message(
    messages: list[dict],
    system: str = None,
    max_tokens: int = 300,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT
) -> str:
    """
    Create a message using the shared client.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system: Optional system prompt
        max_tokens: Maximum tokens in response
        model: Model to use
        timeout: Request timeout in seconds

    Returns:
        The text content of the response.

    Raises:
        anthropic.APITimeoutError: If the request times out
        anthropic.APIError: For other API errors
    """
    client = get_client()

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "timeout": timeout,
    }
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    return response.content[0].text
