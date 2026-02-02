# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""WIA 的 MCP 工具调用封装。"""

import asyncio
from typing import Optional

from mcp import StdioServerParameters
from miroflow_tools.manager import ToolManager

from ..config import settings


class MCPToolClient:
    """封装 WIA 所需的 MCP 工具调用。"""

    def __init__(self) -> None:
        self._manager: Optional[ToolManager] = None

    async def _get_manager(self) -> ToolManager:
        if self._manager is not None:
            return self._manager

        configs = [
            {
                "name": "tool-reading",
                "params": StdioServerParameters(
                    command="python",
                    args=["-m", "miroflow_tools.mcp_servers.reading_mcp_server"],
                ),
            }
        ]

        configs.append(
            {
                "name": "tool-google-search",
                "params": StdioServerParameters(
                    command="python",
                    args=["-m", "miroflow_tools.mcp_servers.searching_google_mcp_server"],
                    env={
                        "JINA_API_KEY": settings.JINA_API_KEY or "",
                        "JINA_BASE_URL": settings.JINA_BASE_URL,
                    },
                ),
            }
        )

        configs.append(
            {
                "name": "tool-wechat-article",
                "params": StdioServerParameters(
                    command="python",
                    args=["-m", "miroflow_tools.mcp_servers.wechat_article_mcp_server"],
                ),
            }
        )

        configs.append(
            {
                "name": "tool-web-scraping",
                "params": StdioServerParameters(
                    command="python",
                    args=["-m", "miroflow_tools.mcp_servers.web_scraping_mcp_server"],
                ),
            }
        )

        self._manager = ToolManager(configs)
        return self._manager

    def convert_to_markdown(self, uri: str) -> str:
        return asyncio.run(self._convert_to_markdown(uri))

    def scrape_website(self, url: str) -> str:
        """
        抓取网站内容，自动识别微信公众号文章。

        Args:
            url: 网站 URL

        Returns:
            抓取的文本内容
        """
        # 检测是否为微信公众号文章链接
        if "mp.weixin.qq.com" in url or "weixin.qq.com" in url:
            return asyncio.run(self._fetch_wechat_article(url))
        # 如果有 JINA API KEY，使用 JINA 抓取
        elif settings.JINA_API_KEY:
            return asyncio.run(self._scrape_website(url))
        # 否则使用纯 Python 抓取
        else:
            return asyncio.run(self._scrape_website_pure(url))

    def scrape_website_pure(self, url: str, extract_links: bool = False) -> str:
        return asyncio.run(self._scrape_website_pure(url, extract_links))

    def scrape_website_raw(self, url: str) -> str:
        return asyncio.run(self._scrape_website_raw(url))

    def fetch_wechat_article(self, url: str) -> str:
        return asyncio.run(self._fetch_wechat_article(url))

    def fetch_wechat_article_raw(self, url: str) -> str:
        return asyncio.run(self._fetch_wechat_article_raw(url))

    async def _convert_to_markdown(self, uri: str) -> str:
        manager = await self._get_manager()
        result = await manager.execute_tool_call(
            server_name="tool-reading",
            tool_name="convert_to_markdown",
            arguments={"uri": uri},
        )
        return result.get("result", "")

    async def _scrape_website(self, url: str) -> str:
        manager = await self._get_manager()
        result = await manager.execute_tool_call(
            server_name="tool-google-search",
            tool_name="scrape_website",
            arguments={"url": url},
        )
        return result.get("result", "")

    async def _fetch_wechat_article(self, url: str) -> str:
        manager = await self._get_manager()
        result = await manager.execute_tool_call(
            server_name="tool-wechat-article",
            tool_name="fetch_wechat_article",
            arguments={"url": url},
        )
        return result.get("result", "")

    async def _fetch_wechat_article_raw(self, url: str) -> str:
        manager = await self._get_manager()
        result = await manager.execute_tool_call(
            server_name="tool-wechat-article",
            tool_name="fetch_wechat_article_raw",
            arguments={"url": url},
        )
        return result.get("result", "")

    async def _scrape_website_pure(self, url: str, extract_links: bool = False) -> str:
        """Scrape website using pure Python (no external API dependencies)."""
        manager = await self._get_manager()
        result = await manager.execute_tool_call(
            server_name="tool-web-scraping",
            tool_name="scrape_website",
            arguments={"url": url, "extract_links": extract_links},
        )
        return result.get("result", "")

    async def _scrape_website_raw(self, url: str) -> str:
        """Scrape website and return raw HTML."""
        manager = await self._get_manager()
        result = await manager.execute_tool_call(
            server_name="tool-web-scraping",
            tool_name="scrape_website_raw",
            arguments={"url": url},
        )
        return result.get("result", "")
