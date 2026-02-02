#!/usr/bin/env python3
"""
基于HTML自动化的封面生成器
使用Playwright自动化操作CoverMaster.html生成封面
"""

import json
import os
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Optional

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("请先安装 Playwright:")
    print("  uv add playwright")
    print("  uv run playwright install chromium")
    exit(1)


class HTMLCoverGenerator:
    """基于HTML的封面生成器"""

    # 风格关键词映射
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

    def __init__(self, html_path: str = 'CoverMaster.html',
                 output_dir: str = 'output/covers'):
        """初始化生成器"""
        self.html_path = Path(html_path).resolve()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.html_path.exists():
            raise FileNotFoundError(f"找不到HTML文件: {self.html_path}")

    def calculate_font_size(self, title: str) -> int:
        """根据标题字数计算字体大小"""
        length = len(title)

        if length <= 8:
            return 140
        elif length <= 12:
            return 120
        elif length <= 16:
            return 75
        elif length <= 20:
            return 85
        elif length <= 25:
            return 70
        else:
            return 54

    def select_style(self, title: str, categories: List[str] = None) -> str:
        """根据标题自动选择风格"""
        style_scores = {style: 0 for style in self.STYLE_KEYWORDS.keys()}

        # 基于关键词匹配
        for style, keywords in self.STYLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title:
                    style_scores[style] += 3

                if categories:
                    for category in categories:
                        if keyword in category:
                            style_scores[style] += 2

        # 如果有匹配，返回最高分
        max_score = max(style_scores.values())
        if max_score > 0:
            return max(style_scores.items(), key=lambda x: x[1])[0]

        # 默认启发式规则
        if any(word in title for word in ['!', '！', '必看', '警告', '注意']):
            return 'shock'
        elif any(word in title for word in ['代码', '编程', '开发', 'AI', '技术']):
            return 'swiss'
        else:
            return 'swiss'  # 默认瑞士风格

    async def setup_page(self, page: Page):
        """设置页面"""
        # 加载HTML
        await page.goto(f'file://{self.html_path}')

        # 等待页面加载完成
        await page.wait_for_selector('#canvas-stage', timeout=5000)

        # 隐藏缩放控件，确保截图尺寸正确
        await page.evaluate('''
            () => {
                const zoomControls = document.querySelector('.absolute.bottom-6');
                if (zoomControls) zoomControls.style.display = 'none';
            }
        ''')

        # 等待一小会儿确保样式渲染完成
        await asyncio.sleep(0.5)

    async def calculate_optimal_font_size(self, page: Page, title: str) -> int:
        """计算最佳字体大小，基于画布区域和文字内容"""
        # 计算最佳字体大小的脚本
        calculate_script = '''
            (titleText) => {
                const stage = document.getElementById('canvas-stage');
                if (!stage) return 80;

                const stageWidth = stage.offsetWidth;
                const stageHeight = stage.offsetHeight;

                // 标题主要占据中间70%的区域
                const targetWidth = stageWidth * 0.7;
                const targetHeight = stageHeight * 0.7;

                // 创建临时元素测量文字
                const tempDiv = document.createElement('div');
                tempDiv.style.visibility = 'hidden';
                tempDiv.style.position = 'absolute';
                tempDiv.style.whiteSpace = 'nowrap';
                tempDiv.style.fontFamily = 'Noto Sans SC, sans-serif';
                tempDiv.style.fontWeight = '900';
                tempDiv.textContent = titleText;
                document.body.appendChild(tempDiv);

                // 测量参考字号（100px）下的文字宽度
                tempDiv.style.fontSize = '100px';
                const textWidthAt100 = tempDiv.offsetWidth;

                document.body.removeChild(tempDiv);

                // 计算最佳字号：确保文字宽度不超过目标宽度
                // 考虑多行情况，假设最多2-3行
                const avgCharsPerLine = titleText.length / 2.5; // 平均每行字符数
                const estimatedLines = Math.ceil(titleText.length / avgCharsPerLine);

                // 计算单行目标宽度
                const singleLineWidth = targetWidth / Math.min(estimatedLines, 3);

                // 根据文字宽度反推字号
                let optimalSize = Math.floor((singleLineWidth / textWidthAt100) * 100);

                // 限制字号范围
                optimalSize = Math.max(30, Math.min(180, optimalSize));

                // 如果文字特别长，进一步调整
                if (titleText.length > 30) {
                    optimalSize = Math.min(optimalSize, 50);
                } else if (titleText.length > 20) {
                    optimalSize = Math.min(optimalSize, 65);
                }

                return optimalSize;
            }
        '''

        optimal_size = await page.evaluate(calculate_script, title)
        return optimal_size

    async def auto_adjust_font_size(self, page: Page, initial_size: int, title: str) -> int:
        """智能计算字体大小，然后微调确保不溢出"""
        min_size = 30  # 最小字体
        max_size = 180  # 最大字体
        current_size = max_size

        # 检测是否溢出的函数
        check_overflow = '''
            (fontSize) => {
                const slider = document.querySelector('input[type="range"]');
                if (!slider) return { overflow: false, size: fontSize };

                slider.value = fontSize;
                slider.dispatchEvent(new Event('input'));

                const stage = document.getElementById('canvas-stage');
                if (!stage) return { overflow: false, size: fontSize };

                const contentLayer = document.getElementById('content-layer');
                const stageRect = stage.getBoundingClientRect();
                const targetTop = stageRect.top + stageRect.height * 0.15;
                const targetBottom = stageRect.bottom - stageRect.height * 0.15;

                let isOverflowing = false;

                if (contentLayer) {
                    const elements = contentLayer.querySelectorAll('*');
                    for (const el of elements) {
                        if (isOverflowing) break;
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;
                        if (rect.left < stageRect.left ||
                            rect.right > stageRect.right ||
                            rect.top < stageRect.top ||
                            rect.bottom > stageRect.bottom) {
                            isOverflowing = true;
                        }
                    }

                    const titles = contentLayer.querySelectorAll('h1');
                    for (const el of titles) {
                        if (isOverflowing) break;
                        const rect = el.getBoundingClientRect();
                        if (rect.height === 0) continue;
                        if (rect.top < targetTop || rect.bottom > targetBottom) {
                            isOverflowing = true;
                        }
                    }
                }

                return {
                    overflow: isOverflowing,
                    size: fontSize,
                    targetTop,
                    targetBottom
                };
            }
        '''

        # 从最大字号开始递减，直到内容不溢出
        while current_size >= min_size:
            result = await page.evaluate(check_overflow, current_size)
            await asyncio.sleep(0.05)
            if not result.get('overflow', False):
                break
            current_size -= 1

        return current_size

    async def generate_single_cover(self, page: Page, article: Dict,
                                    style_override: str = None) -> Optional[str]:
        """生成单个封面"""
        title = article.get('title', '未命名文章')
        summary = article.get('summary', '')
        categories = article.get('categories', [])
        url = article.get('url', '')

        # 生成副标题
        # subtitle = summary[:15] + '...' if len(summary) > 15 else summary
        # if not subtitle:
        subtitle = '精选内容·建议收藏'

        # 选择风格
        style_key = style_override or self.select_style(title, categories)

        # 从最大字号开始递减尝试
        initial_font_size = 180

        try:
            # 1. 输入标题 (使用更精确的选择器)
            title_input = page.locator('input[type="text"]').first
            await title_input.fill(title)
            await asyncio.sleep(0.2)

            # 2. 输入副标题
            await page.fill('textarea', subtitle)
            await asyncio.sleep(0.2)

            # 3. 选择风格
            await page.click(f'button:has-text("{self._get_style_name(style_key)}")')
            await asyncio.sleep(0.3)

            # 4. 智能计算并调整字体大小
            font_size = await self.auto_adjust_font_size(page, initial_font_size, title)
            await asyncio.sleep(0.5)

            # 5. 设置正确的缩放为1（确保1800x1200）
            await page.evaluate('''
                () => {
                    const wrapper = document.getElementById('preview-scale-wrapper');
                    if (wrapper) wrapper.style.transform = 'scale(1)';
                }
            ''')
            await asyncio.sleep(0.3)

            # 6. 截图
            canvas = await page.query_selector('#canvas-stage')
            if not canvas:
                print("✗ 找不到画布元素")
                return None

            # 生成文件名
            file_id = url.split('sn=')[-1][:8] if 'sn=' in url else f"{hash(title)}"
            filename = f"cover_{style_key}_{file_id}.png"
            filepath = self.output_dir / filename

            # 截图并保存
            await canvas.screenshot(path=str(filepath), type='png')

            # 显示调整信息
            if font_size != initial_font_size:
                print(f"✓ 生成封面: {filename}")
                print(f"  标题: {title}")
                print(f"  风格: {self._get_style_name(style_key)}")
                print(f"  字号: {font_size}px (智能计算)")
            else:
                print(f"✓ 生成封面: {filename}")
                print(f"  标题: {title}")
                print(f"  风格: {self._get_style_name(style_key)}")
                print(f"  字号: {font_size}px")

            return str(filepath)

        except Exception as e:
            print(f"✗ 生成失败: {e}")
            return None

    def _get_style_name(self, style_key: str) -> str:
        """获取风格显示名称"""
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
        """批量生成封面"""
        async with async_playwright() as p:
            # 启动浏览器（使用Chromium）
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

            # 设置页面
            await self.setup_page(page)

            print(f"\n开始批量生成封面 (共 {len(articles)} 篇文章)")
            print("=" * 60)

            # 为每篇文章生成封面
            for i, article in enumerate(articles, 1):
                print(f"\n[{i}/{len(articles)}]", end=" ")
                await self.generate_single_cover(page, article, style_override)

            await browser.close()

            print("\n" + "=" * 60)
            print(f"✓ 封面生成完成！保存在: {self.output_dir}")


def load_articles(json_path: str) -> List[Dict]:
    """从JSON文件加载文章数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


async def main_async(args):
    """异步主函数"""
    # 加载文章数据
    if not os.path.exists(args.input):
        print(f"错误: 找不到文件 {args.input}")
        return

    articles = load_articles(args.input)

    if not articles:
        print("错误: 没有找到文章数据")
        return

    # 创建生成器
    generator = HTMLCoverGenerator(
        html_path=args.html,
        output_dir=args.output
    )

    # 批量生成
    await generator.batch_generate(articles, style_override=args.style)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='基于HTML自动化的封面生成器')
    parser.add_argument('-i', '--input', default='output/analyses.json',
                       help='输入JSON文件路径 (默认: output/analyses.json)')
    parser.add_argument('-o', '--output', default='output/covers',
                       help='输出目录 (默认: output/covers)')
    parser.add_argument('--html', default='CoverMaster.html',
                       help='HTML模板文件路径 (默认: CoverMaster.html)')
    parser.add_argument('-s', '--style', default=None,
                       choices=['swiss', 'acid', 'pop', 'shock', 'diffuse',
                               'sticker', 'journal', 'cinema', 'tech',
                               'minimal', 'memo', 'geek'],
                       help='指定风格 (不指定则自动选择)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='无头模式运行 (默认: True)')

    args = parser.parse_args()

    # 运行异步主函数
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
