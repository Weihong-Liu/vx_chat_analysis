#!/usr/bin/env python3
# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
Test script for Website Scraping MCP Tool

This script tests the website scraping functionality through the MCP client.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from wia.tools.mcp_client import MCPToolClient


async def test_scrape_website_async():
    """Test the website scraping functionality (async)."""
    print("=" * 60)
    print("Testing Website Scraping MCP Tool (Async)")
    print("=" * 60)

    client = MCPToolClient()

    # Test URLs
    test_urls = [
        "https://example.com",
        "https://www.python.org",
        "https://github.com",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Test URL: {url}")
        print(f"{'='*60}")

        try:
            result = await client._scrape_website(url)
            print(f"\n✅ Successfully scraped!")
            print(f"Result preview (first 800 chars):\n{result[:800]}...")
            if len(result) > 800:
                print(f"\n... (total {len(result)} characters)")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def test_scrape_website_sync():
    """Test the website scraping functionality (sync)."""
    print("\n" + "=" * 60)
    print("Testing Website Scraping MCP Tool (Sync)")
    print("=" * 60)

    client = MCPToolClient()

    # Test URLs
    test_urls = [
        "https://example.com",
        "https://www.python.org",
        "https://github.com",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Test URL: {url}")
        print(f"{'='*60}")

        try:
            result = client.scrape_website(url)
            print(f"\n✅ Successfully scraped!")
            print(f"Result preview (first 800 chars):\n{result[:800]}...")
            if len(result) > 800:
                print(f"\n... (total {len(result)} characters)")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    print("""
╔════════════════════════════════════════════════════════════╗
║          Website Scraping MCP Tool Test                     ║
║          网站抓取MCP工具测试                                  ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Check if URL is provided as argument
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"Testing single URL: {test_url}\n")

        client = MCPToolClient()

        async def test_single():
            try:
                result = await client._scrape_website(test_url)
                print(f"✅ Successfully scraped!")
                print(f"\nResult:\n{result[:2000]}...")
                if len(result) > 2000:
                    print(f"\n... (total {len(result)} characters)")
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

        asyncio.run(test_single())
    else:
        print("\nUsage: python test_scrape_website.py [url]")
        print("\nExamples:")
        print('  python test_scrape_website.py "https://example.com"')
        print('  python test_scrape_website.py  # Test with default URLs')
        print("\nRunning with default test URLs...\n")

        # Test async version
        asyncio.run(test_scrape_website_async())

        # Test sync version
        test_scrape_website_sync()


if __name__ == "__main__":
    main()
