# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
Simple LLM Client Factory module for WIA.

This module provides a factory function for creating simplified LLM clients
based on configuration. It supports multiple providers including OpenAI,
Anthropic, and other OpenAI-compatible APIs.
"""

from typing import Optional

from .providers.anthropic_client import SimpleAnthropicClient
from .providers.openai_client import SimpleOpenAIClient

# Supported LLM providers
SUPPORTED_PROVIDERS = {"anthropic", "openai", "qwen"}


def SimpleClientFactory(
    provider: str,
    api_key: str,
    model_name: str,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> SimpleOpenAIClient | SimpleAnthropicClient:
    """
    Create a simplified LLM client based on the provider.

    This factory function automatically selects and instantiates the appropriate
    client class based on the provider name.

    Args:
        provider: LLM provider name ("anthropic", "openai", or "qwen")
        api_key: API key for authentication
        model_name: Name of the model to use
        base_url: Optional base URL for custom endpoints
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (default: 2000)

    Returns:
        An instance of the appropriate LLM client

    Raises:
        ValueError: If the provider is not supported

    Example:
        >>> client = SimpleClientFactory(
        ...     provider="anthropic",
        ...     api_key="sk-ant-xxx",
        ...     model_name="claude-3-5-sonnet-20241022"
        ... )
        >>> result = client.generate("Hello, world!")
    """
    client_creators = {
        "anthropic": lambda: SimpleAnthropicClient(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
        "qwen": lambda: SimpleOpenAIClient(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
        "openai": lambda: SimpleOpenAIClient(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    }

    factory = client_creators.get(provider)
    if not factory:
        raise ValueError(
            f"Unsupported provider: '{provider}'. "
            f"Supported providers are: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    return factory()
