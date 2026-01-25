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

# Singleton clients
_sync_client: Optional[anthropic.Anthropic] = None
_async_client: Optional[anthropic.AsyncAnthropic] = None


def get_client() -> anthropic.Anthropic:
    """Get the shared sync Anthropic client. Lazy-loaded on first call."""
    global _sync_client
    if _sync_client is None:
        _sync_client = anthropic.Anthropic(
            timeout=DEFAULT_TIMEOUT
        )
        logger.info("Anthropic sync client initialized")
    return _sync_client


def get_async_client() -> anthropic.AsyncAnthropic:
    """Get the shared async Anthropic client. Lazy-loaded on first call."""
    global _async_client
    if _async_client is None:
        _async_client = anthropic.AsyncAnthropic(
            timeout=DEFAULT_TIMEOUT
        )
        logger.info("Anthropic async client initialized")
    return _async_client


def create_message(
    messages: list[dict],
    system: str = None,
    max_tokens: int = 300,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT
) -> str:
    """
    Create a message using the shared sync client.

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


async def create_message_async(
    messages: list[dict],
    system: str = None,
    max_tokens: int = 300,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT
) -> str:
    """
    Create a message using the shared async client.

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
    client = get_async_client()

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "timeout": timeout,
    }
    if system:
        kwargs["system"] = system

    response = await client.messages.create(**kwargs)
    return response.content[0].text
