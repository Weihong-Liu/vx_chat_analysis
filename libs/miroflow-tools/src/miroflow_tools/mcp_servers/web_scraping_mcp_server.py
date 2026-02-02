# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
Web Scraping MCP Server

A pure Python web scraping tool that doesn't rely on external APIs like Jina.
Uses requests, BeautifulSoup, and optionally Playwright for dynamic content.
"""

import argparse
import logging
import re

import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP

logger = logging.getLogger("miroflow")

# Initialize FastMCP server
mcp = FastMCP("web-scraping-mcp-server")

# Disable warnings
requests.packages.urllib3.disable_warnings()

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 30
MAX_CONTENT_LENGTH = 500000  # Max characters to return


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove multiple whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()


def extract_main_content(soup: BeautifulSoup) -> str:
    """Extract the main content from a webpage."""
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
        script.decompose()

    # Try to find main content area
    main_content = (
        soup.find("main") or
        soup.find("article") or
        soup.find("div", class_=re.compile(r"content|main|article", re.I)) or
        soup.body
    )

    if main_content:
        # Get text content
        text = main_content.get_text(separator="\n", strip=True)
        return clean_text(text)

    return ""


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """Extract metadata from the webpage."""
    metadata = {"url": url}

    # Title
    title_tag = soup.find("title")
    metadata["title"] = title_tag.get_text().strip() if title_tag else ""

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        metadata["description"] = desc_tag.get("content", "")

    # Open Graph metadata
    og_title = soup.find("meta", property="og:title")
    if og_title:
        metadata["og_title"] = og_title.get("content", "")

    og_desc = soup.find("meta", property="og:description")
    if og_desc:
        metadata["og_description"] = og_desc.get("content", "")

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    if canonical:
        metadata["canonical_url"] = canonical.get("href", "")

    return metadata


@mcp.tool()
async def scrape_website(url: str, extract_links: bool = False) -> str:
    """Scrape a website and extract its main content using pure Python.

    This tool fetches web pages and extracts the main content without relying on
    external APIs. It handles static HTML content and provides clean, readable text.

    Args:
        url: The URL of the website to scrape. Must start with http:// or https://
        extract_links: Whether to extract and include links in the output (default: False)

    Returns:
        str: The scraped and formatted website content, including metadata and main text.
             Returns an error message if scraping fails.
    """
    # Validate URL
    if not url or not url.strip():
        return "[ERROR]: URL parameter is required and cannot be empty."

    if not url.startswith(("http://", "https://")):
        return f"[ERROR]: Invalid URL format. URL must start with http:// or https://. Got: {url}"

    # Check for restricted domains
    if "huggingface.co/datasets" in url or "huggingface.co/spaces" in url:
        return "[ERROR]: Cannot scrape Hugging Face datasets/spaces. Please use the official API instead."

    try:
        # Make request
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return f"[ERROR]: Unsupported content type: {content_type}. This tool only supports HTML pages."

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract metadata
        metadata = extract_metadata(soup, url)

        # Extract main content
        content = extract_main_content(soup)

        # Truncate if too long
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH] + "\n\n... (content truncated due to length)"

        # Build result
        result_parts = [
            "# Webpage Content",
            "",
            f"**URL**: {metadata['url']}",
        ]

        if metadata.get("title"):
            result_parts.append(f"**Title**: {metadata['title']}")

        if metadata.get("description"):
            result_parts.append(f"**Description**: {metadata['description']}")

        if metadata.get("canonical_url"):
            result_parts.append(f"**Canonical URL**: {metadata['canonical_url']}")

        result_parts.extend([
            "",
            "---",
            "",
            "# Main Content",
            "",
            content,
        ])

        # Extract links if requested
        if extract_links:
            links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                text = link.get_text().strip()
                if text and href and not href.startswith(("javascript:", "mailto:", "tel:")):
                    links.append(f"- [{text}]({href})")

            if links:
                result_parts.extend([
                    "",
                    "---",
                    "",
                    "# Links Found",
                    "",
                ])
                result_parts.extend(links[:50])  # Limit to 50 links
                if len(links) > 50:
                    result_parts.append(f"\n... and {len(links) - 50} more links")

        return "\n".join(result_parts)

    except requests.exceptions.Timeout:
        return f"[ERROR]: Timeout Error: Request timed out while scraping '{url}'. The website may be slow or unresponsive."

    except requests.exceptions.ConnectionError:
        return f"[ERROR]: Connection Error: Failed to connect to '{url}'. Please check if the URL is correct and accessible."

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "unknown"
        if status_code == 404:
            return f"[ERROR]: Page Not Found (404): The page at '{url}' does not exist."
        elif status_code == 403:
            return f"[ERROR]: Access Forbidden (403): Access to '{url}' is forbidden. The site may require authentication."
        elif status_code == 429:
            return f"[ERROR]: Too Many Requests (429): Rate limited. Please try again later."
        elif status_code == 500:
            return f"[ERROR]: Server Error (500): The server at '{url}' encountered an internal error."
        else:
            return f"[ERROR]: HTTP Error ({status_code}): Failed to scrape '{url}'. {str(e)}"

    except requests.exceptions.RequestException as e:
        return f"[ERROR]: Request Error: Failed to scrape '{url}'. {str(e)}"

    except Exception as e:
        logger.error(f"Unexpected error scraping '{url}': {e}")
        return f"[ERROR]: Unexpected Error: An unexpected error occurred while scraping '{url}': {str(e)}"


@mcp.tool()
async def scrape_website_raw(url: str) -> str:
    """Scrape a website and return the raw HTML content.

    This is a lower-level tool that returns the raw HTML for custom processing.

    Args:
        url: The URL of the website to scrape.

    Returns:
        str: Raw HTML content of the webpage, or an error message if scraping fails.
    """
    # Validate URL
    if not url or not url.strip():
        return "[ERROR]: URL parameter is required and cannot be empty."

    if not url.startswith(("http://", "https://")):
        return f"[ERROR]: Invalid URL format. URL must start with http:// or https://. Got: {url}"

    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT,
            verify=False,
            allow_redirects=True
        )
        response.raise_for_status()

        # Truncate if too long
        html_content = response.text
        if len(html_content) > MAX_CONTENT_LENGTH:
            html_content = html_content[:MAX_CONTENT_LENGTH] + "\n\n... (HTML truncated due to length)"

        return html_content

    except requests.exceptions.Timeout:
        return f"[ERROR]: Timeout Error: Request timed out while scraping '{url}'."

    except requests.exceptions.ConnectionError:
        return f"[ERROR]: Connection Error: Failed to connect to '{url}'."

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        return f"[ERROR]: HTTP Error ({status_code}): Failed to scrape '{url}'. {str(e)}"

    except Exception as e:
        return f"[ERROR]: Unexpected error while scraping '{url}': {str(e)}"


@mcp.tool()
async def scrape_multiple_urls(urls: str) -> str:
    """Scrape multiple URLs and return their combined content.

    Args:
        urls: Comma-separated list of URLs to scrape (e.g., "https://example.com, https://google.com")

    Returns:
        str: Combined content from all URLs, with each URL's content separated by a divider.
    """
    if not urls or not urls.strip():
        return "[ERROR]: URLs parameter is required and cannot be empty."

    # Parse URLs
    url_list = [u.strip() for u in urls.split(",") if u.strip()]

    if not url_list:
        return "[ERROR]: No valid URLs provided."

    if len(url_list) > 10:
        return f"[ERROR]: Too many URLs provided. Maximum 10 URLs allowed. Got: {len(url_list)}"

    results = []

    for i, url in enumerate(url_list, 1):
        results.append(f"\n{'='*60}")
        results.append(f"URL {i}/{len(url_list)}: {url}")
        results.append(f"{'='*60}\n")

        content = await scrape_website(url)
        results.append(content)

        results.append("\n")

    return "\n".join(results)


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Web Scraping MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport method: 'stdio' or 'http' (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to use when running with HTTP transport (default: 8080)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default="/mcp",
        help="URL path to use when running with HTTP transport (default: /mcp)",
    )

    # Parse command line arguments
    args = parser.parse_args()

    # Run the server with the specified transport method
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", port=args.port, path=args.path)
