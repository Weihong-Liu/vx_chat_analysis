#!/usr/bin/env python3
# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
WeChat Official Account Article Fetcher Tool
微信公众号文章获取工具

This module provides tools for fetching WeChat official account articles.
It can be used as a standalone CLI tool or imported as a module.
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Disable warnings
requests.packages.urllib3.disable_warnings()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("wechat_article_fetcher")

# Generate user agent
try:
    USER_AGENT = UserAgent().chrome
except Exception:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class WeChatArticleFetcher:
    """
    WeChat Official Account Article Fetcher

    This class provides functionality to fetch articles from WeChat official accounts.
    """

    def __init__(self, output_dir: str = "articles"):
        """
        Initialize the fetcher.

        Args:
            output_dir: Directory to save fetched articles
        """
        self.session = requests.Session()
        self.timeout = 10
        self.headers = {"User-Agent": USER_AGENT}
        self.output_dir = output_dir
        self.cookies = {}
        self.nickname = ""
        self.public_main_link = ""
        self.biz = ""

        os.makedirs(self.output_dir, exist_ok=True)

    def delay_short_time(self):
        """Add short delay to avoid being blocked."""
        import random
        import time
        second_num = round(random.uniform(0.1, 1.5), 3)
        logger.info(f"Short delay: {second_num}s")
        time.sleep(second_num)

    def get_an_article(self, content_url: str) -> dict:
        """
        Fetch a single WeChat article.

        Args:
            content_url: WeChat article URL

        Returns:
            dict with content_flag (1 for success) and content
        """
        try:
            content_url = content_url.replace('amp;', '')
            res = self.session.get(
                url=content_url,
                headers=self.headers,
                cookies=self.cookies,
                verify=False,
                timeout=self.timeout
            )
            self.delay_short_time()

            if "var createTime = " in res.text:
                logger.info("Successfully fetched article")
                return {"content_flag": 1, "content": res.text}
            elif ">当前环境异常, 完成验证后即可继续访问 <" in res.text:
                logger.error("Environment abnormal, verification required")
                return {"content_flag": 0, "current_url": content_url, "error": "verification_required"}
            elif "操作频繁, 请稍后再试" in res.text:
                logger.error("Operation too frequent")
                return {"content_flag": 0, "current_url": content_url, "error": "too_frequent"}
            else:
                logger.error(f"Unknown error for URL: {content_url}")
                return {"content_flag": 0, "current_url": content_url, "error": "unknown"}
        except Exception as e:
            logger.error(f"Exception during fetch: {e}")
            return {"content_flag": 0, "current_url": content_url, "error": str(e)}

    def format_content(self, content: str) -> dict:
        """
        Format article content and extract metadata.

        Args:
            content: Article HTML content

        Returns:
            dict with formatted article information
        """
        soup = BeautifulSoup(content, "lxml")

        # Extract metadata
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

    def fetch_article(self, url: str) -> Optional[dict]:
        """
        Fetch and parse an article.

        Args:
            url: Article URL

        Returns:
            Article info dict or None if failed
        """
        logger.info(f"{'='*60}")
        logger.info(f"Fetching article: {url}")
        logger.info(f"{'='*60}")

        result = self.get_an_article(url)

        if result["content_flag"] == 1:
            article_info = self.format_content(result["content"])
            return article_info
        else:
            logger.error(f"Failed to fetch article: {url}")
            return None

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage."""
        # Replace invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    def save_as_json(self, article_info: dict) -> str:
        """Save article as JSON format."""
        create_time = article_info["createTime"].replace(":", "_")
        title = self.sanitize_filename(article_info["article_title"])

        filename = f"{create_time} ---- {title}.json"
        filepath = os.path.join(self.output_dir, filename)

        data = {
            "title": article_info["article_title"],
            "author": article_info["author"],
            "nickname": article_info["nickname"],
            "url": article_info["article_link"],
            "create_time": article_info["createTime"],
            "content_lines": article_info["format_texts"],
            "public_main_link": self.public_main_link,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved to: {filepath}")
        return filepath

    def save_as_markdown(self, article_info: dict) -> str:
        """Save article as Markdown format."""
        create_time = article_info["createTime"].replace(":", "_")
        title = self.sanitize_filename(article_info["article_title"])

        filename = f"{create_time} ---- {title}.md"
        filepath = os.path.join(self.output_dir, filename)

        content = f"""# {article_info['article_title']}

**Author**: {article_info['author']}
**Official Account**: {article_info['nickname']}
**Publish Time**: {article_info['createTime']}
**Article URL**: {article_info['article_link']}

---

"""

        for line in article_info["format_texts"]:
            content += line + "\n\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Saved to: {filepath}")
        return filepath

    def save_as_txt(self, article_info: dict) -> str:
        """Save article as plain text format."""
        create_time = article_info["createTime"].replace(":", "_")
        title = self.sanitize_filename(article_info["article_title"])

        filename = f"{create_time} ---- {title}.txt"
        filepath = os.path.join(self.output_dir, filename)

        content = f"""{'='*60}
Title: {article_info['article_title']}
Author: {article_info['author']}
Official Account: {article_info['nickname']}
Publish Time: {article_info['createTime']}
Article URL: {article_info['article_link']}
{'='*60}

"""

        for line in article_info["format_texts"]:
            content += line + "\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Saved to: {filepath}")
        return filepath

    def fetch_and_save(self, url: str, save_format: str = "md") -> Optional[str]:
        """
        Fetch and save an article.

        Args:
            url: Article URL
            save_format: Save format ('json', 'md', 'txt')

        Returns:
            Saved file path or None if failed
        """
        article_info = self.fetch_article(url)

        if article_info is None:
            return None

        if save_format == "json":
            return self.save_as_json(article_info)
        elif save_format == "txt":
            return self.save_as_txt(article_info)
        else:
            return self.save_as_markdown(article_info)


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="WeChat Official Account Article Fetcher"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="WeChat article URL"
    )
    parser.add_argument(
        "-o", "--output",
        default="articles",
        help="Output directory (default: articles)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["md", "json", "txt"],
        default="md",
        help="Output format (default: md)"
    )

    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════════╗
║          WeChat Article Fetcher                             ║
║          微信公众号文章获取工具                               ║
╚════════════════════════════════════════════════════════════╝
    """)

    # Get URL if not provided
    url = args.url
    if not url:
        url = input("Please enter WeChat article URL: ").strip()

    if not url:
        logger.error("URL cannot be empty!")
        return 1

    # Create fetcher and fetch
    fetcher = WeChatArticleFetcher(output_dir=args.output)
    filepath = fetcher.fetch_and_save(url, args.format)

    if filepath:
        print(f"\n{'='*60}")
        print("Success!")
        print(f"File saved to: {os.path.abspath(filepath)}")
        print(f"{'='*60}")
        return 0
    else:
        print("\nFailed to fetch article. Please check the URL!")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
