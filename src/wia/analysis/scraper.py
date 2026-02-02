# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""为链接抓取网页内容。"""

import logging
from typing import Iterable, List
from urllib.parse import urlparse

from ..core.models import LinkItem
from ..tools.mcp_client import MCPToolClient

logger = logging.getLogger(__name__)


class LinkScraper:
    """抓取链接对应内容（尽力而为），失败时使用XML元数据兜底。"""

    def __init__(self) -> None:
        self._client = MCPToolClient()

    def _classify_link(self, url: str, title: str = None, description: str = None) -> List[str]:
        """
        根据URL域名、标题和描述对链接进行分类。

        返回类别列表（支持多选）。
        """
        categories = []

        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            # URL解析失败，使用简单模式匹配
            domain = ""

        # 域名分类
        if "mp.weixin.qq.com" in url:
            categories.append("微信公众号")
        elif domain and ("github.com" in domain or "gitlab.com" in domain):
            categories.append("代码仓库")
        elif domain and "zhihu.com" in domain:
            categories.append("知乎")
        elif domain and ("bilibili.com" in domain or "youtube.com" in domain):
            categories.append("视频")
        elif domain and "juejin.cn" in domain:
            categories.append("技术文章")
        elif domain and "csdn.net" in domain:
            categories.append("技术文章")
        elif domain and "stackoverflow.com" in domain:
            categories.append("技术问答")

        # 标题/描述关键词分类
        text = f"{title or ''} {description or ''}".lower()

        # 技术相关
        tech_keywords = ["ai", "代码", "开发", "编程", "算法", "数据", "系统", "工具",
                        "python", "java", "javascript", "golang", "rust", "前端", "后端",
                        "人工智能", "机器学习", "深度学习"]
        if any(keyword in text for keyword in tech_keywords):
            categories.append("技术")

        # 产品相关
        product_keywords = ["产品", "设计", "用户体验", "ui", "ux"]
        if any(keyword in text for keyword in product_keywords):
            categories.append("产品")

        # 职场相关
        career_keywords = ["职场", "面试", "求职", "薪资", "职业", "成长"]
        if any(keyword in text for keyword in career_keywords):
            categories.append("职场")

        # 资讯/新闻
        news_keywords = ["新闻", "资讯", "发布", "更新", "最新"]
        if any(keyword in text for keyword in news_keywords):
            categories.append("资讯")

        # 教程/指南
        tutorial_keywords = ["教程", "指南", "入门", "如何", "怎么", "实战"]
        if any(keyword in text for keyword in tutorial_keywords):
            categories.append("教程")

        if not categories:
            categories.append("未分类")

        return list(set(categories))  # 去重

    def run(self, links: Iterable[LinkItem]) -> List[LinkItem]:
        enriched: List[LinkItem] = []

        for link in links:
            # 尝试爬取网页内容
            try:
                text = self._client.scrape_website(link.url)
                if text:
                    link.text = text
                    logger.debug(f"成功爬取: {link.url}")
                else:
                    logger.info(f"爬取返回空内容，使用XML元数据兜底: {link.url}")
            except Exception as e:
                logger.warning(f"爬取失败: {link.url}, 错误: {e}, 使用XML元数据兜底")

            # 兜底策略：如果爬取失败且XML元数据存在，使用XML中的标题和描述
            if not link.text and link.xml_metadata:
                # 组合标题和描述作为文本内容
                fallback_parts = []
                if link.title:
                    fallback_parts.append(f"标题: {link.title}")
                if link.description:
                    fallback_parts.append(f"描述: {link.description}")

                if fallback_parts:
                    link.text = "\n".join(fallback_parts)
                    logger.info(f"使用XML元数据兜底成功: {link.url}")

            # 分类
            link.categories = self._classify_link(
                link.url,
                link.title,
                link.description
            )

            enriched.append(link)

        return enriched
