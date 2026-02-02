#!/usr/bin/env python3
# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
Test script for Web Scraping MCP Tool (Pure Python)

This script tests the web scraping functionality that doesn't rely on
external APIs like Jina. It uses pure Python libraries (requests, BeautifulSoup).
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from wia.tools.mcp_client import MCPToolClient


async def test_scrape_website_pure():
    """Test the pure Python web scraping functionality (async)."""
    print("=" * 60)
    print("Testing Web Scraping MCP Tool (Pure Python - Async)")
    print("=" * 60)

    client = MCPToolClient()

    # Test URLs - static websites that work well with requests
    test_urls = [
        "https://example.com",
        "https://www.python.org",
        "https://httpbin.org/html",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Test URL: {url}")
        print(f"{'='*60}")

        try:
            result = await client._scrape_website_pure(url)
            print(f"\n✅ Successfully scraped!")
            print(f"Result preview (first 1000 chars):\n{result[:1000]}...")
            if len(result) > 1000:
                print(f"\n... (total {len(result)} characters)")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_scrape_website_pure_with_links():
    """Test the web scraping with link extraction (async)."""
    print("\n" + "=" * 60)
    print("Testing Web Scraping with Link Extraction (Async)")
    print("=" * 60)

    client = MCPToolClient()
    test_url = "https://example.com"

    print(f"\nTest URL: {test_url}")
    print("Extracting links...")

    try:
        result = await client._scrape_website_pure(test_url, extract_links=True)
        print(f"\n✅ Successfully scraped with links!")
        print(f"\nResult:\n{result[:2000]}...")
        if len(result) > 2000:
            print(f"\n... (total {len(result)} characters)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_scrape_website_raw():
    """Test the raw HTML scraping functionality (async)."""
    print("\n" + "=" * 60)
    print("Testing Raw HTML Scraping (Async)")
    print("=" * 60)

    client = MCPToolClient()
    test_url = "https://example.com"

    print(f"\nTest URL: {test_url}")

    try:
        result = await client._scrape_website_raw(test_url)
        print(f"\n✅ Successfully scraped raw HTML!")
        print(f"HTML length: {len(result)} characters")
        print(f"\nPreview (first 500 chars):\n{result[:500]}...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_scrape_website_pure_sync():
    """Test the web scraping functionality (sync)."""
    print("\n" + "=" * 60)
    print("Testing Web Scraping MCP Tool (Pure Python - Sync)")
    print("=" * 60)

    client = MCPToolClient()

    test_urls = [
        "https://example.com",
        "https://www.python.org",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Test URL: {url}")
        print(f"{'='*60}")

        try:
            result = client.scrape_website_pure(url)
            print(f"\n✅ Successfully scraped!")
            print(f"Result preview (first 1000 chars):\n{result[:1000]}...")
            if len(result) > 1000:
                print(f"\n... (total {len(result)} characters)")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    print("""
╔════════════════════════════════════════════════════════════╗
║          Web Scraping MCP Tool Test                         ║
║          纯Python网页爬取MCP工具测试 (无需外部API)            ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Check if URL is provided as argument
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"Testing single URL: {test_url}\n")

        client = MCPToolClient()

        async def test_single():
            try:
                result = await client._scrape_website_pure(test_url)
                print(f"✅ Successfully scraped!")
                print(f"\nResult:\n{result[:3000]}...")
                if len(result) > 3000:
                    print(f"\n... (total {len(result)} characters)")
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

        asyncio.run(test_single())
    else:
        print("\nUsage: python test_web_scraping.py [url]")
        print("\nExamples:")
        print('  python test_web_scraping.py "https://example.com"')
        print('  python test_web_scraping.py  # Test with default URLs')
        print("\nRunning with default test URLs...\n")

        # Test async versions
        asyncio.run(test_scrape_website_pure())
        asyncio.run(test_scrape_website_pure_with_links())
        asyncio.run(test_scrape_website_raw())

        # Test sync version
        test_scrape_website_pure_sync()


if __name__ == "__main__":
    main()
