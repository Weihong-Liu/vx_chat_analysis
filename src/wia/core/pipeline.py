# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
WIA 管道编排器。

负责串联读取、分析与存储等阶段。
"""

import json
import logging
from pathlib import Path
from typing import List

from .models import ChatMessage, LinkAnalysis
from ..analysis.data_cleaner import DataCleaner
from ..analysis.deduplicator import LinkDeduplicator
from ..analysis.cover_generator import generate_covers
from ..analysis.link_filter import LinkFilter
from ..analysis.feishu_publisher import FeishuPublisher
from ..analysis.keyword_scorer import KeywordScorer
from ..analysis.link_extractor import LinkExtractor
from ..analysis.llm_summarizer import LinkSummarizer
from ..analysis.scraper import LinkScraper
from ..analysis.topic_builder import TopicBuilder
from ..analysis.user_profiler import UserProfiler
from ..storage.store import JsonStore

logger = logging.getLogger(__name__)


class Pipeline:
    """编排离线分析管道。"""

    def __init__(
        self,
        output_dir: Path,
        enable_feishu: bool = False,
        enable_cleaning: bool = True,
    ) -> None:
        """
        初始化管道。

        Args:
            output_dir: 输出目录
            enable_feishu: 是否启用飞书发布
            enable_cleaning: 是否启用数据清洗
        """
        self.output_dir = output_dir
        self.enable_cleaning = enable_cleaning

        # 初始化各个处理阶段
        self.cleaner = DataCleaner() if enable_cleaning else None
        self.extractor = LinkExtractor()
        self.link_filter = LinkFilter()
        self.deduplicator = LinkDeduplicator()
        self.scraper = LinkScraper()
        self.summarizer = LinkSummarizer()
        self.scorer = KeywordScorer()
        self.topic_builder = TopicBuilder()
        self.user_profiler = UserProfiler()
        self.store = JsonStore(output_dir=output_dir)
        self.feishu_publisher = FeishuPublisher(enabled=enable_feishu)

    def run(self, loader) -> None:
        """执行完整的分析管道。"""
        messages: List[ChatMessage] = loader.load()

        logger.info("=" * 60)
        logger.info("开始执行 WIA 分析管道")
        logger.info("=" * 60)
        logger.info(f"已加载 {len(messages)} 条消息")

        # ========== 阶段0: 数据清洗 ==========
        if self.cleaner:
            logger.info("")
            logger.info("[阶段0] 数据清洗")
            messages = self.cleaner.run(messages)

        # ========== 阶段1: 提取链接 ==========
        logger.info("")
        logger.info("[阶段1] 提取链接")
        links = self.extractor.run(messages)
        logger.info(f"提取到 {len(links)} 个链接")

        # ========== 阶段2: 链接过滤 ==========
        logger.info("")
        logger.info("[阶段2] 链接过滤")
        links = self.link_filter.run(links)
        logger.info(f"过滤后 {len(links)} 个链接")

        # ========== 阶段3: 链接去重 ==========
        logger.info("")
        logger.info("[阶段3] 链接去重")
        links = self.deduplicator.run(links)
        logger.info(f"去重后 {len(links)} 个链接")

        analyses = []
        # ========== 阶段4: 抓取内容 ==========
        logger.info("")
        logger.info("[阶段4] 抓取链接内容")
        links = self.scraper.run(links)

        # ========== 阶段5: LLM 分析 ==========
        logger.info("")
        logger.info("[阶段5] LLM 分析链接")
        analyses = self.summarizer.run(links)

        # ========== 阶段6: 关键词评分 ==========
        logger.info("")
        logger.info("[阶段6] 关键词评分")
        analyses = self.scorer.run(analyses)

        # ========== 阶段7: 话题构建 ==========
        logger.info("")
        logger.info("[阶段7] 构建话题")
        topics = self.topic_builder.run(messages)

        # ========== 阶段8: 用户画像 ==========
        logger.info("")
        logger.info("[阶段8] 构建用户画像")
        profiles = self.user_profiler.run(messages, analyses)

        # ========== 阶段9: 存储到本地 ==========
        logger.info("")
        logger.info("[阶段9] 存储到本地")
        self.store.write_links(links)
        self.store.write_analyses(analyses)
        self.store.write_topics(topics)
        self.store.write_profiles(profiles)
        
        # analyses = self._load_analyses()
        # ========== 阶段9: 生成封面（可选）==========
        cover_map = {}
        logger.info("")
        logger.info("[阶段9] 生成封面")
        if self.feishu_publisher.enabled:
            cover_map = self._generate_covers(analyses)
        else:
            logger.info("× 飞书发布未启用，跳过封面生成")

        # ========== 阶段10: 发布到飞书（可选）==========
        logger.info("")
        logger.info("[阶段10] 发布到飞书")
        if self.feishu_publisher.enabled:
            published_count = self.feishu_publisher.run(analyses, cover_map=cover_map)
            logger.info(f"✓ 已发布 {published_count} 条记录到飞书")
        else:
            logger.info("× 飞书发布未启用")

        logger.info("")
        logger.info("=" * 60)
        logger.info("WIA 分析管道执行完成")
        logger.info("=" * 60)

    def close(self) -> None:
        """清理资源。"""
        if self.summarizer:
            self.summarizer.close()
        if self.feishu_publisher:
            self.feishu_publisher.close()

    def _generate_covers(self, analyses: list) -> dict:
        root_dir = Path(__file__).resolve().parents[3]
        html_path = root_dir / "src/wia/tools/CoverMaster2.html"
        output_dir = self.output_dir / "covers"

        try:
            return generate_covers(analyses, html_path=html_path, output_dir=output_dir)
        except Exception as exc:
            logger.warning("封面生成失败，跳过该阶段: %s", exc)
            return {}

    def _load_analyses(self) -> List[LinkAnalysis]:
        analyses_path = self.output_dir / "analyses.json"
        if not analyses_path.exists():
            return []

        raw_items = json.loads(analyses_path.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            raw_items = [raw_items]

        analyses: List[LinkAnalysis] = []
        for item in raw_items:
            analyses.append(
                LinkAnalysis(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    categories=item.get("categories", []),
                    score=int(item.get("score", 0) or 0),
                    reason=item.get("reason", ""),
                    sender=item.get("sender"),
                    created_at=item.get("created_at"),
                    cover_style=item.get("cover_style"),
                )
            )

        return analyses
