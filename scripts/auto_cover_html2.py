#!/usr/bin/env python3
"""
基于HTML自动化的封面生成器（CoverMaster2 版）
使用页面内置 Auto-Fit，不做复杂字号判断
"""

import json
import os
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Optional

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("请先安装 Playwright:")
    print("  uv add playwright")
    print("  uv run playwright install chromium")
    exit(1)


class HTMLCoverGeneratorV2:
    """基于CoverMaster2的封面生成器"""

    STYLE_KEYWORDS = {
        'swiss': ['技术', '工具', '开发', 'AI', '编程', '代码', '框架'],
        'acid': ['设计', '创意', '艺术', '潮流', '前卫'],
        'pop': ['新闻', '热点', '娱乐', '有趣', '趋势'],
        'shock': ['警告', '重要', '必看', '紧急', '注意'],
        'diffuse': ['生活', '健康', '情感', '故事', '清新'],
        'sticker': ['可爱', '轻松', '小技巧', '日常', '简单'],
        'journal': ['日记', '记录', '思考', '感悟', '文艺'],
        'cinema': ['深度', '电影', '故事', '专题', '叙事'],
        'tech': ['科技', '数据', '分析', '报告', '研究'],
        'minimal': ['极简', '设计', '美学', '纯粹'],
        'memo': ['笔记', '清单', '总结', '备忘', '实用'],
        'geek': ['黑客', '极客', '编程', '开发', '系统'],
    }

    def __init__(self, html_path: str = 'CoverMaster2.html',
                 output_dir: str = 'output/covers'):
        self.html_path = Path(html_path).resolve()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.html_path.exists():
            raise FileNotFoundError(f"找不到HTML文件: {self.html_path}")

    def select_style(self, title: str, categories: List[str] = None) -> str:
        """根据标题自动选择风格"""
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

        if any(word in title for word in ['!', '！', '必看', '警告', '注意']):
            return 'shock'
        if any(word in title for word in ['代码', '编程', '开发', 'AI', '技术']):
            return 'swiss'
        return 'swiss'

    async def setup_page(self, page: Page):
        await page.goto(f'file://{self.html_path}')
        await page.wait_for_selector('#canvas-stage', timeout=5000)

        await page.evaluate('''
            () => {
                const zoomControls = document.querySelector('.absolute.bottom-6');
                if (zoomControls) zoomControls.style.display = 'none';
            }
        ''')
        await asyncio.sleep(0.5)

    async def enable_auto_fit(self, page: Page):
        await page.evaluate('''
            () => {
                if (window.app && typeof window.app.updateState === 'function') {
                    window.app.updateState('autoFit', true);
                }
            }
        ''')

    async def generate_single_cover(self, page: Page, article: Dict,
                                    style_override: str = None) -> Optional[str]:
        title = article.get('title', '未命名文章')
        categories = article.get('categories', [])
        url = article.get('url', '')

        subtitle = '精选内容·建议收藏'
        style_key = style_override or self.select_style(title, categories)

        try:
            title_input = page.locator('input[type="text"]').first
            await title_input.fill(title)
            await asyncio.sleep(0.2)

            await page.fill('textarea', subtitle)
            await asyncio.sleep(0.2)

            await page.click(f'button:has-text("{self._get_style_name(style_key)}")')
            await asyncio.sleep(0.3)

            await self.enable_auto_fit(page)
            await asyncio.sleep(0.3)

            await page.evaluate('''
                () => {
                    const wrapper = document.getElementById('preview-scale-wrapper');
                    if (wrapper) wrapper.style.transform = 'scale(1)';
                }
            ''')
            await asyncio.sleep(0.2)

            canvas = await page.query_selector('#canvas-stage')
            if not canvas:
                print("✗ 找不到画布元素")
                return None

            file_id = url.split('sn=')[-1][:8] if 'sn=' in url else f"{hash(title)}"
            filename = f"cover_{style_key}_{file_id}.png"
            filepath = self.output_dir / filename

            await canvas.screenshot(path=str(filepath), type='png')

            print(f"✓ 生成封面: {filename}")
            print(f"  标题: {title}")
            print(f"  风格: {self._get_style_name(style_key)}")
            print("  字号: Auto-Fit")

            return str(filepath)
        except Exception as e:
            print(f"✗ 生成失败: {e}")
            return None

    def _get_style_name(self, style_key: str) -> str:
        style_names = {
            'swiss': '🇨🇭 瑞士国际',
            'acid': '💚 故障酸性',
            'pop': '🎨 波普撞色',
            'shock': '⚡️ 冲击波',
            'diffuse': '🌈 弥散光',
            'sticker': '🍭 贴纸风',
            'journal': '📝 手账感',
            'cinema': '🎬 电影感',
            'tech': '🔵 科技蓝',
            'minimal': '⚪️ 极简白',
            'memo': '🟡 备忘录',
            'geek': '🟢 极客黑',
        }
        return style_names.get(style_key, style_key)

    async def batch_generate(self, articles: List[Dict],
                            style_override: str = None):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

            await self.setup_page(page)

            print(f"\n开始批量生成封面 (共 {len(articles)} 篇文章)")
            print("=" * 60)

            for i, article in enumerate(articles, 1):
                print(f"\n[{i}/{len(articles)}]", end=" ")
                await self.generate_single_cover(page, article, style_override)

            await browser.close()

            print("\n" + "=" * 60)
            print(f"✓ 封面生成完成！保存在: {self.output_dir}")


def load_articles(json_path: str) -> List[Dict]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


async def main_async(args):
    if not os.path.exists(args.input):
        print(f"错误: 找不到文件 {args.input}")
        return

    articles = load_articles(args.input)
    if not articles:
        print("错误: 没有找到文章数据")
        return

    generator = HTMLCoverGeneratorV2(
        html_path=args.html,
        output_dir=args.output
    )

    await generator.batch_generate(articles, style_override=args.style)


def main():
    parser = argparse.ArgumentParser(description='基于CoverMaster2的封面生成器')
    parser.add_argument('-i', '--input', default='output/analyses.json',
                       help='输入JSON文件路径 (默认: output/analyses.json)')
    parser.add_argument('-o', '--output', default='output/covers2',
                       help='输出目录 (默认: output/covers2)')
    parser.add_argument('--html', default='CoverMaster2.html',
                       help='HTML模板文件路径 (默认: CoverMaster2.html)')
    parser.add_argument('-s', '--style', default=None,
                       choices=['swiss', 'acid', 'pop', 'shock', 'diffuse',
                               'sticker', 'journal', 'cinema', 'tech',
                               'minimal', 'memo', 'geek'],
                       help='指定风格 (不指定则自动选择)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='无头模式运行 (默认: True)')

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
