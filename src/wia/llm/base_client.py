# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
Base client module for LLM providers.

This module defines the abstract base class and common utilities for LLM clients,
supporting both OpenAI and Anthropic API formats (simplified for WIA use case).
"""

import dataclasses
from abc import ABC
from typing import Any, Dict, List, Optional, TypedDict


class TokenUsage(TypedDict, total=True):
    """
    Unified token usage tracking across different LLM providers.

    Simplified version for WIA - only tracks input and output tokens.
    """

    total_input_tokens: int
    total_output_tokens: int


@dataclasses.dataclass
class SimpleBaseClient(ABC):
    """
    Abstract base class for simplified LLM provider clients.

    This class provides a common interface for interacting with different LLM providers
    (OpenAI, Anthropic, etc.) for simple text generation tasks like link summarization.

    Attributes:
        api_key: API key for authentication
        base_url: Optional base URL for custom endpoints
        model_name: Name of the model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
    """

    # Required arguments
    api_key: str
    model_name: str

    # Optional arguments (with default value)
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000

    # Initialized in __post_init__
    client: Any = dataclasses.field(init=False)
    token_usage: TokenUsage = dataclasses.field(init=False)

    def __post_init__(self):
        """Initialize the client and token usage tracker."""
        self.token_usage = self._reset_token_usage()
        self.client = self._create_client()

    def _reset_token_usage(self) -> TokenUsage:
        """
        Reset token usage counter to zero.

        Returns:
            A new TokenUsage dict with all counters set to zero.
        """
        return TokenUsage(
            total_input_tokens=0,
            total_output_tokens=0,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text (sync interface).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            Generated text
        """
        raise NotImplementedError("Subclasses must implement generate()")

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text (async interface).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            Generated text
        """
        raise NotImplementedError("Subclasses must implement agenerate()")

    def _create_client(self) -> Any:
        """Create the underlying client instance."""
        raise NotImplementedError("Subclasses must implement _create_client()")

    def _update_token_usage(self, usage_data: Any) -> None:
        """Update cumulative token usage."""
        if usage_data:
            self.token_usage["total_input_tokens"] += getattr(usage_data, "input_tokens", getattr(usage_data, "prompt_tokens", 0)) or 0
            self.token_usage["total_output_tokens"] += getattr(usage_data, "output_tokens", getattr(usage_data, "completion_tokens", 0)) or 0

    def close(self) -> None:
        """Close client connection."""
        if hasattr(self.client, "close"):
            self.client.close()

    def get_token_usage(self) -> TokenUsage:
        """Get current token usage statistics."""
        return self.token_usage.copy()
