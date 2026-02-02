# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

import argparse
import logging
import os
import re
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from fastmcp import FastMCP

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger("miroflow")

# Initialize FastMCP server
mcp = FastMCP("wechat-article-mcp-server")

# Generate random user agent
try:
    USER_AGENT = UserAgent().chrome
except Exception:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class WeChatArticleFetcher:
    """WeChat Official Account Article Fetcher"""

    def __init__(self):
        self.session = requests.Session()
        self.timeout = 10
        self.headers = {"User-Agent": USER_AGENT}
        self.nickname = ""
        self.public_main_link = ""

    def get_an_article(self, content_url: str) -> dict:
        """
        Fetch a single WeChat article.

        Args:
            content_url: WeChat article URL (permanent link or short link)

        Returns:
            dict with keys: content_flag (1 for success, 0 for failure),
                           content (article HTML), current_url
        """
        try:
            content_url = content_url.replace('amp;', '')
            res = self.session.get(
                url=content_url,
                headers=self.headers,
                cookies={},
                verify=False,
                timeout=self.timeout
            )

            # Validate response
            if "var createTime = " in res.text:
                logger.info("Successfully fetched article content")
                return {"content_flag": 1, "content": res.text}
            elif ">当前环境异常, 完成验证后即可继续访问 <" in res.text:
                logger.error("Environment abnormal, verification required")
                return {"content_flag": 0, "current_url": content_url, "error": "Verification required"}
            elif "操作频繁, 请稍后再试" in res.text:
                logger.error("Operation too frequent, please try again later")
                return {"content_flag": 0, "current_url": content_url, "error": "Operation too frequent"}
            else:
                logger.error(f"Unknown error occurred for URL: {content_url}")
                return {"content_flag": 0, "current_url": content_url, "error": "Unknown error"}
        except Exception as e:
            logger.error(f"Exception during fetch: {e}")
            return {"content_flag": 0, "current_url": content_url, "error": str(e)}

    def format_content(self, content: str) -> dict:
        """
        Format article content, extract text and metadata.

        Args:
            content: Article HTML content

        Returns:
            dict with article metadata and formatted content
        """
        soup = BeautifulSoup(content, "lxml")

        # Extract article metadata
        self.nickname = soup.find("a", id="js_name").get_text().strip()
        author = soup.find("meta", {"name": "author"}).get("content").strip()
        article_link = soup.find("meta", property="og:url").get("content")
        article_title = soup.find("h1", id="activity-name").get_text().strip()

        logger.info(f"Current article: {article_title}")

        # Extract text content
        original_texts = soup.getText().split("\n")
        format_texts = list(filter(lambda x: bool(x.strip()), original_texts))

        # Extract create time
        createTime = re.search(r"var createTime = '(.*?)'.*", content).group(1)
        year, month, day = createTime.split(" ")[0].split("-")
        hour, minute = createTime.split(" ")[1].split(":")

        # Extract biz value and construct main link
        appuin = re.search(r"var appuin = (.*?);", content).group(1)
        quoted_values = re.findall(r'["\']([^"\']*)["\']', appuin)
        for value in quoted_values:
            if value:
                self.biz = value
                break

        self.public_main_link = (
            "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz="
            + self.biz
            + "&scene=124#wechat_redirect"
        )

        return {
            "nickname": self.nickname,
            "author": author,
            "article_link": article_link,
            "article_title": article_title,
            "createTime": createTime,
            "content": content,
            "format_texts": format_texts,
            "public_main_link": self.public_main_link,
        }


# Global fetcher instance
_fetcher: Optional[WeChatArticleFetcher] = None


def get_fetcher() -> WeChatArticleFetcher:
    """Get or create the global fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = WeChatArticleFetcher()
    return _fetcher


@mcp.tool()
async def fetch_wechat_article(url: str) -> str:
    """Fetch a WeChat official account article and return its content.

    This tool fetches articles from WeChat official accounts (微信公众号).
    It extracts the article title, author, content, and metadata.

    Args:
        url: Required. The URL of the WeChat article to fetch.
              Should be a valid WeChat MP article URL (mp.weixin.qq.com).

    Returns:
        str: JSON string containing article information including:
             - title: Article title
             - author: Article author
             - nickname: Official account name
             - url: Article URL
             - create_time: Article publish time
             - content_lines: List of article content lines
             - public_main_link: Official account main page link
             Or an error message if the fetch fails.
    """
    if not url or not url.strip():
        return "[ERROR]: URL parameter is required and cannot be empty."

    # Validate URL format
    if "mp.weixin.qq.com" not in url:
        return "[ERROR]: Invalid URL. URL should be from mp.weixin.qq.com"

    fetcher = get_fetcher()

    try:
        # Fetch article content
        result = fetcher.get_an_article(url)

        if result["content_flag"] != 1:
            error_msg = result.get("error", "Unknown error")
            return f"[ERROR]: Failed to fetch article: {error_msg}"

        # Format article content
        article_info = fetcher.format_content(result["content"])

        # Build response as formatted JSON-like string
        response_lines = [
            "# WeChat Article Information",
            "",
            f"**Title**: {article_info['article_title']}",
            f"**Author**: {article_info['author']}",
            f"**Official Account**: {article_info['nickname']}",
            f"**Publish Time**: {article_info['createTime']}",
            f"**Article URL**: {article_info['article_link']}",
            f"**Account Home**: {article_info['public_main_link']}",
            "",
            "---",
            "",
            "# Article Content",
            "",
        ]

        # Add article content lines
        for line in article_info["format_texts"]:
            response_lines.append(line)

        return "\n".join(response_lines)

    except Exception as e:
        logger.error(f"Error processing article: {e}")
        return f"[ERROR]: Failed to process article: {str(e)}"


@mcp.tool()
async def fetch_wechat_article_raw(url: str) -> str:
    """Fetch a WeChat article and return raw content for further processing.

    This is a lower-level tool that returns the raw HTML content of a WeChat article.
    Useful when you need to parse the content yourself or extract specific elements.

    Args:
        url: Required. The URL of the WeChat article to fetch.

    Returns:
        str: Raw HTML content of the article, or an error message if fetch fails.
    """
    if not url or not url.strip():
        return "[ERROR]: URL parameter is required and cannot be empty."

    if "mp.weixin.qq.com" not in url:
        return "[ERROR]: Invalid URL. URL should be from mp.weixin.qq.com"

    fetcher = get_fetcher()

    try:
        result = fetcher.get_an_article(url)

        if result["content_flag"] != 1:
            error_msg = result.get("error", "Unknown error")
            return f"[ERROR]: Failed to fetch article: {error_msg}"

        return result["content"]

    except Exception as e:
        logger.error(f"Error fetching article: {e}")
        return f"[ERROR]: Failed to fetch article: {str(e)}"


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="WeChat Article MCP Server")
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
