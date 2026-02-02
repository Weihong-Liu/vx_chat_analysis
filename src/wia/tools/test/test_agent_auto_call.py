#!/usr/bin/env python3
# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
AI Agent Auto-Call Test for WeChat Article MCP Tool

This script demonstrates how an AI Agent can automatically decide when to call
the WeChat article fetch tool based on user input.
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from wia.tools.mcp_client import MCPToolClient
from wia.config import settings


class Tool:
    """Represents a tool that the agent can use."""

    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class SimpleAgent:
    """
    A simple AI Agent that can automatically decide when to call tools.

    This implementation uses OpenAI-compatible API for function calling.
    """

    def __init__(self, tools: List[Tool]):
        self.tools = tools
        self.mcp_client = MCPToolClient()
        self.llm_config = {
            "base_url": settings.LLM_BASE_URL or "https://api.openai.com/v1",
            "api_key": settings.LLM_API_KEY or "",
            "model": settings.LLM_MODEL_NAME or "gpt-4o-mini"
        }

        # Lazy import of OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.llm_config["api_key"],
                base_url=self.llm_config["base_url"]
            )
        except ImportError:
            print("Warning: openai package not installed. Install with: pip install openai")
            self.client = None
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI client: {e}")
            self.client = None

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent."""
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])

        return f"""You are a helpful AI assistant with access to the following tools:

{tool_descriptions}

When a user's request can be fulfilled by one of these tools, use the appropriate tool.
If no tool is relevant, respond with general conversation.

Available tools:
{json.dumps([tool.to_dict() for tool in self.tools], indent=2, ensure_ascii=False)}

Rules:
1. Only use tools when the user's request specifically requires them
2. For WeChat article URLs, always use fetch_wechat_article
3. For general websites, use scrape_website
4. Always provide helpful responses based on the tool results
"""

    def _extract_wechat_url(self, message: str) -> Optional[str]:
        """Extract WeChat article URL from message."""
        # Match WeChat article URLs
        pattern = r'https://mp\.weixin\.qq\.com/s/[a-zA-Z0-9_/\-?=]+'
        match = re.search(pattern, message)
        return match.group(0) if match else None

    def _extract_general_url(self, message: str) -> Optional[str]:
        """Extract general URL from message."""
        pattern = r'https?://[^\s]+'
        match = re.search(pattern, message)
        return match.group(0) if match else None

    def _decide_tool(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Decide which tool to use based on user message (rule-based approach).

        Args:
            user_message: The user's input message

        Returns:
            dict with tool_name and parameters, or None if no tool needed
        """
        message_lower = user_message.lower()

        # Check for WeChat article
        wechat_url = self._extract_wechat_url(user_message)
        if wechat_url:
            return {
                "tool_name": "fetch_wechat_article",
                "parameters": {"url": wechat_url}
            }

        # Check for general website scraping keywords
        if any(keyword in message_lower for keyword in ["抓取", "获取", "scrape", "fetch", "网页", "website"]):
            general_url = self._extract_general_url(user_message)
            if general_url and "mp.weixin.qq.com" not in general_url:
                return {
                    "tool_name": "scrape_website",
                    "parameters": {"url": general_url}
                }

        # Check for document conversion keywords
        if any(keyword in message_lower for keyword in ["转换", "convert", "markdown", "文档"]):
            # Look for file paths or URIs
            uri_pattern = r'(file:|data:)[^\s]+'
            match = re.search(uri_pattern, user_message)
            if match:
                return {
                    "tool_name": "convert_to_markdown",
                    "parameters": {"uri": match.group(0)}
                }

        return None

    def _call_tool(self, tool_name: str, parameters: dict) -> str:
        """Execute a tool call."""
        try:
            if tool_name == "fetch_wechat_article":
                return self.mcp_client.fetch_wechat_article(**parameters)
            elif tool_name == "fetch_wechat_article_raw":
                return self.mcp_client.fetch_wechat_article_raw(**parameters)
            elif tool_name == "scrape_website":
                return self.mcp_client.scrape_website(**parameters)
            elif tool_name == "convert_to_markdown":
                return self.mcp_client.convert_to_markdown(**parameters)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"

    def _call_with_llm(self, user_message: str) -> str:
        """Use LLM to decide which tool to call (if available)."""
        if self.client is None:
            return "LLM client not available. Please set LLM_API_KEY and LLM_BASE_URL environment variables."

        try:
            # Create tools schema for OpenAI
            functions = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                }
                for tool in self.tools
            ]

            # Call LLM with function calling
            response = self.client.chat.completions.create(
                model=self.llm_config["model"],
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": user_message}
                ],
                tools=functions,
                tool_choice="auto"
            )

            message = response.choices[0].message

            # Check if the model wants to call a function
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                # Execute the tool
                result = self._call_tool(tool_name, arguments)

                # Send result back to LLM for final response
                followup = self.client.chat.completions.create(
                    model=self.llm_config["model"],
                    messages=[
                        {"role": "system", "content": self._create_system_prompt()},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": None, "tool_calls": [tool_call]},
                        {"role": "tool", "tool_call_id": tool_call.id, "content": result[:5000]}  # Truncate if too long
                    ]
                )
                return followup.choices[0].message.content
            else:
                return message.content

        except Exception as e:
            return f"Error in LLM call: {str(e)}"

    def run(self, user_message: str, use_llm: bool = False) -> str:
        """
        Process user message and return agent's response.

        Args:
            user_message: The user's input message
            use_llm: If True, use LLM for decision making. If False, use rule-based.

        Returns:
            The agent's response
        """
        print(f"\n{'='*60}")
        print(f"User: {user_message}")
        print(f"{'='*60}")

        if use_llm:
            print("\n🤖 Using LLM-based agent...")
            response = self._call_with_llm(user_message)
            print(f"\nAgent: {response}")
            return response
        else:
            print("\n🔧 Using rule-based agent...")
            tool_decision = self._decide_tool(user_message)

            if tool_decision:
                print(f"\n🎯 Decided to use tool: {tool_decision['tool_name']}")
                print(f"📋 Parameters: {tool_decision['parameters']}")

                result = self._call_tool(
                    tool_decision["tool_name"],
                    tool_decision["parameters"]
                )

                # Provide a summary response
                if tool_decision["tool_name"] == "fetch_wechat_article":
                    response = f"✅ Successfully fetched WeChat article!\n\n{result[:1000]}..."
                elif tool_decision["tool_name"] == "scrape_website":
                    response = f"✅ Successfully scraped website!\n\n{result[:1000]}..."
                else:
                    response = f"✅ Tool execution result:\n\n{result[:1000]}..."

                print(f"\nAgent: {response}")
                return response
            else:
                # No tool needed, provide a general response
                response = "I understand your request, but I don't have a specific tool for that task."
                print(f"\nAgent: {response}")
                return response


def main():
    """Main entry point for testing."""
    print("""
╔════════════════════════════════════════════════════════════╗
║          AI Agent Auto-Call Test                           ║
║          微信文章MCP工具 - Agent自动调用测试                ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Define available tools
    tools = [
        Tool(
            name="fetch_wechat_article",
            description="获取微信公众号文章内容，提取标题、作者、正文等信息",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "微信公众号文章链接 (mp.weixin.qq.com)"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="fetch_wechat_article_raw",
            description="获取微信公众号文章的原始HTML内容",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "微信公众号文章链接"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="scrape_website",
            description="抓取并提取网页内容",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "网页URL"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="convert_to_markdown",
            description="将文档转换为Markdown格式",
            parameters={
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "文档URI (file: 或 data:)"
                    }
                },
                "required": ["uri"]
            }
        )
    ]

    # Create agent
    agent = SimpleAgent(tools)

    # Test cases
    test_cases = [
        {
            "description": "WeChat Article URL",
            "message": "帮我获取这篇微信文章的内容：https://mp.weixin.qq.com/s/GuNKq9PBi5BnfpsfV627FQ?scene=1&click_id=76"
        },
        {
            "description": "WeChat Article (shortened request)",
            "message": "分析一下这篇文章 https://mp.weixin.qq.com/s/GuNKq9PBi5BnfpsfV627FQ?scene=1&click_id=76"
        },
        {
            "description": "General conversation (no tool needed)",
            "message": "你好，今天天气怎么样？"
        },
        {
            "description": "Website scraping",
            "message": "抓取 https://example.com 的内容"
        }
    ]

    print("\n" + "="*60)
    print("Available modes:")
    print("  1. Rule-based Agent (规则匹配 - 无需LLM)")
    print("  2. LLM-based Agent (需要 LLM_API_KEY)")
    print("="*60 + "\n")

    # Check which mode to use
    use_llm = "--llm" in sys.argv or "-l" in sys.argv

    if use_llm:
        if not settings.LLM_API_KEY:
            print("⚠️  Warning: LLM_API_KEY not set. Falling back to rule-based mode.")
            use_llm = False
        else:
            print("✅ Using LLM-based agent mode")
            print(f"   Model: {agent.llm_config['model']}")
            print(f"   Base URL: {agent.llm_config['base_url']}\n")
    else:
        print("✅ Using rule-based agent mode (no LLM required)\n")

    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'#'*60}")
        print(f"Test {i}: {test['description']}")
        print(f"{'#'*60}")

        agent.run(test["message"], use_llm=use_llm)

        print("\n" + "-"*60 + "\n")

    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("""
Usage: python test_agent_auto_call.py [options]

Options:
  --llm, -l    Use LLM-based agent (requires LLM_API_KEY env var)
  --help, -h   Show this help message

Examples:
  # Rule-based mode (no LLM required)
  python test_agent_auto_call.py

  # LLM-based mode (requires LLM_API_KEY)
  export LLM_API_KEY="your-api-key"
  export LLM_BASE_URL="https://api.openai.com/v1"
  export LLM_MODEL_NAME="gpt-4o-mini"
  python test_agent_auto_call.py --llm
        """)
        sys.exit(0)

    main()
