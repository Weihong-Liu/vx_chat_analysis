# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
OpenAI-compatible LLM client implementation (simplified for WIA).

This module provides the SimpleOpenAIClient class for interacting with OpenAI's API
and OpenAI-compatible endpoints for simple text generation tasks.

Features:
- Sync and async API support
- Token usage tracking
- Simple text generation interface
"""

import dataclasses
import logging
from typing import Any, Optional

from openai import AsyncOpenAI, OpenAI

from ..base_client import SimpleBaseClient

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SimpleOpenAIClient(SimpleBaseClient):
    """Simplified OpenAI client for WIA link summarization."""

    base_url: Optional[str] = None

    def _create_client(self) -> OpenAI:
        """Create OpenAI client."""
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _create_async_client(self) -> AsyncOpenAI:
        """Create async OpenAI client."""
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using OpenAI API.

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

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                temperature=temp,
                max_tokens=max_tok,
                messages=messages,
            )

            # Update token usage
            self._update_token_usage(getattr(response, "usage", None))

            logger.info(
                f"OpenAI API call successful, "
                f"input tokens: {response.usage.prompt_tokens}, "
                f"output tokens: {response.usage.completion_tokens}"
            )

            content = response.choices[0].message.content or ""
            return content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using OpenAI API (async).

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

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async_client = self._create_async_client()

        try:
            response = await async_client.chat.completions.create(
                model=self.model_name,
                temperature=temp,
                max_tokens=max_tok,
                messages=messages,
            )

            # Update token usage
            self._update_token_usage(getattr(response, "usage", None))

            logger.info(
                f"OpenAI async API call successful, "
                f"input tokens: {response.usage.prompt_tokens}, "
                f"output tokens: {response.usage.completion_tokens}"
            )

            content = response.choices[0].message.content or ""
            return content

        except Exception as e:
            logger.error(f"OpenAI async API call failed: {e}")
            raise
        finally:
            await async_client.close()
