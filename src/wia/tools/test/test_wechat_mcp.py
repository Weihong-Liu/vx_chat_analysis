#!/usr/bin/env python3
# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
Test script for WeChat Article MCP Tool

This script tests the WeChat article fetch functionality through the MCP client.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from wia.tools.mcp_client import MCPToolClient


async def test_wechat_article_fetch():
    """Test the WeChat article fetch functionality."""
    print("=" * 60)
    print("Testing WeChat Article MCP Tool")
    print("=" * 60)

    client = MCPToolClient()

    # Test URL (replace with actual WeChat article URL for testing)
    test_url = "https://mp.weixin.qq.com/s/GuNKq9PBi5BnfpsfV627FQ?scene=1&click_id=76"

    print(f"\nTest URL: {test_url}")
    print("\n1. Testing fetch_wechat_article...")

    try:
        result = await client._fetch_wechat_article(test_url)
        print(f"Result preview (first 500 chars):\n{result[:500]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n2. Testing fetch_wechat_article_raw...")

    try:
        result = await client._fetch_wechat_article_raw(test_url)
        print(f"Raw HTML length: {len(result)} characters")
        print(f"Preview (first 200 chars):\n{result[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_sync_wrapper():
    """Test the synchronous wrapper methods."""
    print("\n" + "=" * 60)
    print("Testing Synchronous Wrapper Methods")
    print("=" * 60)

    client = MCPToolClient()
    test_url = "https://mp.weixin.qq.com/s/GuNKq9PBi5BnfpsfV627FQ?scene=1&click_id=76"

    print(f"\nTest URL: {test_url}")
    print("\n1. Testing fetch_wechat_article (sync)...")

    try:
        result = client.fetch_wechat_article(test_url)
        print(f"Result preview (first 500 chars):\n{result[:500]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    # Check if URL is provided as argument
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        print("\nUsage: python test_wechat_mcp.py <wechat_article_url>")
        print("\nExample:")
        print('  python test_wechat_mcp.py "https://mp.weixin.qq.com/s/GuNKq9PBi5BnfpsfV627FQ?scene=1&click_id=76"')
        print("\nRunning with default placeholder URL...")
        test_url = "https://mp.weixin.qq.com/s/GuNKq9PBi5BnfpsfV627FQ?scene=1&click_id=76"

    print("=" * 60)
    print("WeChat Article MCP Tool Test")
    print("=" * 60)

    # Test async version
    print("\n--- Testing Async Version ---")
    client = MCPToolClient()

    async def async_test():
        print(f"\nTest URL: {test_url}")
        print("\nTesting fetch_wechat_article (async)...")

        try:
            result = await client._fetch_wechat_article(test_url)
            print(f"Result preview (first 500 chars):\n{result}...")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(async_test())

    # # Test sync version
    # print("\n--- Testing Sync Wrapper ---")
    # try:
    #     result = client.fetch_wechat_article(test_url)
    #     print(f"Result preview (first 500 chars):\n{result[:500]}...")
    # except Exception as e:
    #     print(f"Error: {e}")
    #     import traceback
    #     traceback.print_exc()


if __name__ == "__main__":
    main()
