# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""自动生成封面并返回 URL -> 封面路径映射。"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
    from playwright.async_api import async_playwright, Page
except ImportError:  # pragma: no cover - optional dependency
    async_playwright = None
    Page = None

from ..core.models import LinkAnalysis

logger = logging.getLogger(__name__)


class HTMLCoverGeneratorV2:
    """基于 CoverMaster2 的封面生成器。"""

    STYLE_KEYWORDS = {
        "swiss": ["技术", "工具", "开发", "AI", "编程", "代码", "框架"],
        "acid": ["设计", "创意", "艺术", "潮流", "前卫"],
        "pop": ["新闻", "热点", "娱乐", "有趣", "趋势"],
        "shock": ["警告", "重要", "必看", "紧急", "注意"],
        "diffuse": ["生活", "健康", "情感", "故事", "清新"],
        "sticker": ["可爱", "轻松", "小技巧", "日常", "简单"],
        "journal": ["日记", "记录", "思考", "感悟", "文艺"],
        "cinema": ["深度", "电影", "故事", "专题", "叙事"],
        "tech": ["科技", "数据", "分析", "报告", "研究"],
        "minimal": ["极简", "设计", "美学", "纯粹"],
        "memo": ["笔记", "清单", "总结", "备忘", "实用"],
        "geek": ["黑客", "极客", "编程", "开发", "系统"],
    }

    def __init__(self, html_path: Path, output_dir: Path) -> None:
        self.html_path = html_path.resolve()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.html_path.exists():
            raise FileNotFoundError(f"找不到HTML文件: {self.html_path}")

    def select_style(self, title: str, categories: List[str] | None = None) -> str:
        style_scores = {style: 0 for style in self.STYLE_KEYWORDS.keys()}

        for style, keywords in self.STYLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title:
                    style_scores[style] += 3
                if categories:
                    for category in categories:
                        if keyword in category:
                            style_scores[style] += 2

        max_score = max(style_scores.values())
        if max_score > 0:
            return max(style_scores.items(), key=lambda x: x[1])[0]

        if any(word in title for word in ["!", "！", "必看", "警告", "注意"]):
            return "shock"
        if any(word in title for word in ["代码", "编程", "开发", "AI", "技术"]):
            return "swiss"
        return "swiss"

    async def setup_page(self, page: Page) -> None:
        await page.goto(f"file://{self.html_path}")
        await page.wait_for_selector("#canvas-stage", timeout=5000)

        await page.evaluate(
            """
            () => {
                const zoomControls = document.querySelector('.absolute.bottom-6');
                if (zoomControls) zoomControls.style.display = 'none';
            }
            """
        )
        await asyncio.sleep(0.5)

    async def enable_auto_fit(self, page: Page) -> None:
        await page.evaluate(
            """
            () => {
                if (window.app && typeof window.app.updateState === 'function') {
                    window.app.updateState('autoFit', true);
                }
            }
            """
        )

    async def generate_single_cover(
        self,
        page: Page,
        analysis: LinkAnalysis,
        style_override: str | None = None,
    ) -> Optional[str]:
        title = analysis.title or "未命名文章"
        categories = analysis.categories or []
        url = analysis.url or ""

        subtitle = "精选内容·建议收藏"
        style_key = style_override
        if not style_key and analysis.cover_style in self.STYLE_KEYWORDS:
            style_key = analysis.cover_style
        if not style_key:
            style_key = self.select_style(title, categories)

        logger.debug("Generating cover: title=%s url=%s style=%s", title, url, style_key)

        try:
            title_input = page.locator('input[type="text"]').first
            await title_input.fill(title)
            await asyncio.sleep(0.2)

            await page.fill("textarea", subtitle)
            await asyncio.sleep(0.2)

            await page.click(f'button:has-text("{self._get_style_name(style_key)}")')
            await asyncio.sleep(0.3)

            await self.enable_auto_fit(page)
            await asyncio.sleep(0.3)

            await page.evaluate(
                """
                () => {
                    const wrapper = document.getElementById('preview-scale-wrapper');
                    if (wrapper) wrapper.style.transform = 'scale(1)';
                }
                """
            )
            await asyncio.sleep(0.2)

            canvas = await page.query_selector("#canvas-stage")
            if not canvas:
                logger.debug("Cover generation skipped: canvas not found for title=%s", title)
                return None

            file_id = url.split("sn=")[-1][:8] if "sn=" in url else f"{hash(title)}"
            filename = f"cover_{style_key}_{file_id}.png"
            filepath = self.output_dir / filename

            logger.debug("Cover output path: %s", filepath)
            await canvas.screenshot(path=str(filepath), type="png")

            return str(filepath)
        except Exception as exc:
            logger.warning("Cover generation failed for %s: %s", title, exc)
            return None

    def _get_style_name(self, style_key: str) -> str:
        style_names = {
            "swiss": "🇨🇭 瑞士国际",
            "acid": "💚 故障酸性",
            "pop": "🎨 波普撞色",
            "shock": "⚡️ 冲击波",
            "diffuse": "🌈 弥散光",
            "sticker": "🍭 贴纸风",
            "journal": "📝 手账感",
            "cinema": "🎬 电影感",
            "tech": "🔵 科技蓝",
            "minimal": "⚪️ 极简白",
            "memo": "🟡 备忘录",
            "geek": "🟢 极客黑",
        }
        return style_names.get(style_key, style_key)

    async def batch_generate(
        self,
        analyses: Iterable[LinkAnalysis],
        style_override: str | None = None,
    ) -> Dict[str, str]:
        covers: Dict[str, str] = {}

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})

            await self.setup_page(page)

            for analysis in analyses:
                cover_path = await self.generate_single_cover(page, analysis, style_override)
                if cover_path:
                    covers[analysis.url] = cover_path

            await browser.close()

        return covers


def generate_covers(
    analyses: Iterable[LinkAnalysis],
    html_path: Path,
    output_dir: Path,
    style_override: str | None = None,
) -> Dict[str, str]:
    if async_playwright is None:
        logger.warning("Playwright is not installed; skip cover generation")
        return {}

    generator = HTMLCoverGeneratorV2(html_path=html_path, output_dir=output_dir)
    return asyncio.run(generator.batch_generate(analyses, style_override=style_override))
