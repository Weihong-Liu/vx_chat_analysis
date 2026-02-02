# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
Anthropic Claude LLM client implementation (simplified for WIA).

This module provides the SimpleAnthropicClient class for interacting with Anthropic's
Claude API for simple text generation tasks.

Features:
- Sync and async API support
- Token usage tracking
- Simple text generation interface
"""

import dataclasses
import logging
from typing import Any, Optional

from anthropic import Anthropic, AsyncAnthropic

from ..base_client import SimpleBaseClient

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SimpleAnthropicClient(SimpleBaseClient):
    """Simplified Anthropic client for WIA link summarization."""

    base_url: Optional[str] = None

    def _create_client(self) -> Anthropic:
        """Create Anthropic client."""
        return Anthropic(api_key=self.api_key, base_url=self.base_url)

    def _create_async_client(self) -> AsyncAnthropic:
        """Create async Anthropic client."""
        return AsyncAnthropic(api_key=self.api_key, base_url=self.base_url)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Anthropic API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        messages = [{"role": "user", "content": prompt}]

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "temperature": temp,
            "max_tokens": max_tok,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.client.messages.create(**kwargs)

            # Update token usage
            self._update_token_usage(getattr(response, "usage", None))

            logger.info(
                f"Anthropic API call successful, "
                f"input tokens: {response.usage.input_tokens}, "
                f"output tokens: {response.usage.output_tokens}"
            )

            # Extract text content
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text

            return content

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Anthropic API (async).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        messages = [{"role": "user", "content": prompt}]

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "temperature": temp,
            "max_tokens": max_tok,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        async_client = self._create_async_client()

        try:
            response = await async_client.messages.create(**kwargs)

            # Update token usage
            self._update_token_usage(getattr(response, "usage", None))

            logger.info(
                f"Anthropic async API call successful, "
                f"input tokens: {response.usage.input_tokens}, "
                f"output tokens: {response.usage.output_tokens}"
            )

            # Extract text content
            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text

            return content

        except Exception as e:
            logger.error(f"Anthropic async API call failed: {e}")
            raise
        finally:
            await async_client.close()
