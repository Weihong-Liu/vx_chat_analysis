# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""生成链接摘要。"""

import json
import logging
from typing import Iterable, List, Optional

from json_repair import repair_json

from ..config.settings import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL_NAME,
    LLM_PROVIDER,
)
from ..core.models import LinkAnalysis, LinkItem
from ..llm import SimpleClientFactory

logger = logging.getLogger(__name__)


class LinkSummarizer:
    """使用 LLM 生成链接摘要和分析。"""

    COVER_STYLES = [
        "swiss",
        "acid",
        "pop",
        "shock",
        "diffuse",
        "sticker",
        "journal",
        "cinema",
        "tech",
        "minimal",
        "memo",
        "geek",
    ]

    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的内容分析助手，负责分析分享的链接并生成高质量的摘要。

你的任务是：
1. 提取或生成链接的标题（简洁明了，不超过 50 字）
2. 生成简洁明了的中文摘要（不超过 150 字）
3. 判断链接的内容类别（支持多选）
4. 根据内容价值打分（0-100 分）
5. 选择封面风格（cover_style），从给定列表中选一个

内容类别包括（可以多选）：
- 技术文档: 编程、AI、开发工具等技术相关
- 文章博客: 个人博客、观点文章等
- 新闻资讯: 技术新闻、行业动态等
- 学习资源: 教程、课程、文档等
- 实用工具: 在线工具、软件服务等
- 产品介绍: 产品发布、更新说明等
- 其他: 不符合以上分类的内容

封面风格可选值：
- swiss, acid, pop, shock, diffuse, sticker, journal, cinema, tech, minimal, memo, geek

请以 JSON 格式返回结果：
{
    "title": "标题",
    "summary": "摘要内容",
    "categories": ["类别1", "类别2"],
    "score": 分数,
    "reason": "打分理由",
    "cover_style": "swiss"
}

注意：
- title: 如果链接本身有标题则直接使用，否则生成一个
- summary: 简洁概括链接内容
- categories: 选择 1-3 个最相关的类别
- score: 0-100 分，根据内容的实用性和价值打分
- cover_style: 从给定风格列表中选一个最匹配的"""

    def __init__(self, enable_llm: bool = True):
        """
        初始化 LinkSummarizer。

        Args:
            enable_llm: 是否启用 LLM，如果为 False 则使用简单的 fallback 模式
        """
        self.enable_llm = enable_llm and bool(LLM_API_KEY)
        self._client: Optional[SimpleClientFactory] = None

        if self.enable_llm:
            try:
                self._client = SimpleClientFactory(
                    provider=LLM_PROVIDER or "anthropic",
                    api_key=LLM_API_KEY,
                    base_url=LLM_BASE_URL,
                    model_name=LLM_MODEL_NAME or "claude-3-5-sonnet-20241022",
                    temperature=0.5,
                    max_tokens=1000,
                )
                logger.info("LinkSummarizer LLM mode enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client, using fallback mode: {e}")
                self.enable_llm = False
        else:
            logger.info("LinkSummarizer using fallback mode")

    def run(self, links: Iterable[LinkItem]) -> List[LinkAnalysis]:
        """
        为链接列表生成分析。

        Args:
            links: 链接列表

        Returns:
            链接分析列表
        """
        if self.enable_llm and self._client:
            return self._llm_analyze(links)
        else:
            return self._fallback_analyze(links)

    def _llm_analyze(self, links: Iterable[LinkItem]) -> List[LinkAnalysis]:
        """使用 LLM 分析链接。"""
        import time
        analyses: List[LinkAnalysis] = []
        links_list = list(links)  # 转换为列表以便获取索引和总数

        logger.info(f"Starting LLM analysis for {len(links_list)} links")

        for idx, link in enumerate(links_list, 1):
            logger.info(f"[{idx}/{len(links_list)}] Analyzing: {link.url}")
            try:
                prompt = self._build_prompt(link)
                logger.debug(f"Prompt built for {link.url}")

                response = self._client.generate(
                    prompt=prompt,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=0.5,
                    max_tokens=800,
                )

                logger.debug(f"LLM response received for {link.url}, length: {len(response)}")
                logger.debug(f"Raw LLM response: {response[:200]}...")

                # 解析 JSON 响应
                try:
                    result = json.loads(response)
                    logger.debug(f"JSON parsed successfully with json.loads")
                except json.JSONDecodeError as e:
                    logger.warning(f"Standard JSON parsing failed: {e}, attempting json-repair")

                    try:
                        # 使用 json-repair 尝试修复
                        repaired_json = repair_json(response, skip_json_loads=False, return_objects=False)
                        logger.debug(f"JSON repaired successfully")
                        logger.debug(f"Repaired JSON: {repaired_json[:200]}...")
                        result = json.loads(repaired_json)
                    except Exception as repair_error:
                        logger.error(f"JSON repair also failed: {repair_error}")
                        logger.error(f"Failed response: {response}")
                        # 使用 fallback
                        title = link.title or self._extract_title_from_url(link.url)
                        summary = self._fallback_summary(link)
                        categories = ["其他"]
                        score = 0
                        reason = "json-parse-failed"

                        # 组装分享者
                        sender = link.senders # link.senders[0] if link.senders else None

                        analyses.append(
                            LinkAnalysis(
                                url=link.url,
                                title=title,
                                summary=summary,
                                categories=categories,
                                score=score,
                                reason=reason,
                                sender=sender,
                                created_at=link.created_at,
                                cover_style=None,
                            )
                        )
                        continue

                # 提取字段
                title = result.get("title", link.title or "")
                summary = result.get("summary", "")
                categories = result.get("categories", ["其他"])
                score = int(result.get("score", 0))
                reason = result.get("reason", "")
                cover_style = result.get("cover_style")
                if cover_style not in self.COVER_STYLES:
                    cover_style = None

                # 确保 categories 是列表
                if isinstance(categories, str):
                    categories = [categories]

                # 组装分享者和创建时间
                sender = link.senders # link.senders[0] if link.senders else None

                logger.info(f"[{idx}/{len(links_list)}] ✓ Parsed: title={title[:30]}, categories={categories}, score={score}")

                analyses.append(
                    LinkAnalysis(
                        url=link.url,
                        title=title,
                        summary=summary,
                        categories=categories,
                        score=score,
                        reason=reason,
                        sender=sender,
                        created_at=link.created_at,
                        cover_style=cover_style,
                    )
                )

            except Exception as e:
                logger.error(f"[{idx}/{len(links_list)}] ✗ LLM analysis failed: {link.url}, error: {e}", exc_info=True)

                # 使用 fallback
                title = link.title or self._extract_title_from_url(link.url)
                summary = self._fallback_summary(link)
                categories = ["其他"]
                sender = link.senders # link.senders[0] if link.senders else None

                analyses.append(
                    LinkAnalysis(
                        url=link.url,
                        title=title,
                        summary=summary,
                        categories=categories,
                        score=0,
                        reason="llm-error",
                        sender=sender,
                        created_at=link.created_at,
                        cover_style=None,
                    )
                )

        logger.info(f"LLM analysis completed: {len(analyses)} links processed")
        return analyses

    def _fallback_analyze(self, links: Iterable[LinkItem]) -> List[LinkAnalysis]:
        """使用简单的 fallback 方式分析链接。"""
        import time
        analyses: List[LinkAnalysis] = []

        for link in links:
            title = link.title or self._extract_title_from_url(link.url)
            summary = self._fallback_summary(link)
            sender = link.senders # link.senders[0] if link.senders else None

            analyses.append(
                LinkAnalysis(
                    url=link.url,
                    title=title,
                    summary=summary,
                    categories=["其他"],
                    score=0,
                    reason="fallback-mode",
                    sender=sender,
                    created_at=link.created_at,
                    cover_style=None,
                )
            )
        return analyses

    def _extract_title_from_url(self, url: str) -> str:
        """从 URL 中提取简单的标题。"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            path = parsed.path.strip("/")

            if path:
                # 获取路径的最后一部分作为标题
                parts = path.split("/")
                title = parts[-1] if parts else path
                # 去除扩展名
                if "." in title:
                    title = title.rsplit(".", 1)[0]
                return title.replace("-", " ").replace("_", " ")

            # 如果没有路径，返回域名
            return parsed.netloc
        except Exception:
            return url[:50]  # 降级返回前 50 个字符

    def _build_prompt(self, link: LinkItem) -> str:
        """构建 LLM 提示词。"""
        prompt_parts = [f"链接 URL: {link.url}"]

        if link.title:
            prompt_parts.append(f"标题: {link.title}")

        if link.senders:
            prompt_parts.append(f"分享者: {', '.join(link.senders)}")

        if link.contexts:
            # 取前 3 个上下文示例
            contexts = link.contexts[:3]
            context_text = "\n".join(f"- {ctx[:100]}" for ctx in contexts)
            prompt_parts.append(f"分享上下文:\n{context_text}")

        if link.text:
            # 抓取的内容可能很长，只取前 2000 字
            text_preview = link.text[:2000]
            if len(link.text) > 2000:
                text_preview += "..."
            prompt_parts.append(f"链接内容预览:\n{text_preview}")

        return "\n\n".join(prompt_parts)

    def _fallback_summary(self, link: LinkItem) -> str:
        """生成简单的 fallback 摘要。"""
        if link.title:
            return link.title
        if link.text:
            # 取前 200 字作为摘要
            text = link.text[:200].replace("\n", " ")
            if len(link.text) > 200:
                text += "..."
            return text
        return link.url

    def close(self) -> None:
        """关闭客户端连接。"""
        if self._client:
            self._client.close()
