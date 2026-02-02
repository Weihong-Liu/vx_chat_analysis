# HTML自动化封面生成器

基于CoverMaster.html的自动化封面生成工具，使用Playwright控制浏览器生成高质量封面。

## 功能特性

- ✅ **完整复用HTML风格**：直接使用CoverMaster.html的所有12种精美风格
- ✅ **自动风格选择**：根据标题关键词和分类智能匹配风格
- ✅ **智能字体调整**：根据标题字数自动调整字号
- ✅ **批量生成**：一次处理多篇文章
- ✅ **高清输出**：1800×1200 PNG格式

## 依赖安装

### 方法1：快速安装（推荐）

如果Playwright自动下载太慢，可以手动下载：

```bash
# 1. 添加Playwright依赖
uv add playwright

# 2. 手动下载浏览器（从Playwright GitHub Releases）
# 下载地址：https://github.com/microsoft/playwright/releases
# 需要下载：
#   - chromium-{version}-mac.zip (Chrome浏览器)
#   - chromium-headless-shell-mac-arm64.zip (Headless Shell，ARM Mac)

# 3. 解压到Playwright缓存目录
unzip chromium-{version}-mac.zip
mkdir -p ~/Library/Caches/ms-playwright/chromium-1200
mv chromium-*/Google\ Chrome\ for\ Testing.app ~/Library/Caches/ms-playwright/chromium-1200/

unzip chromium-headless-shell-mac-arm64.zip
mkdir -p ~/Library/Caches/ms-playwright/chromium_headless_shell-1200
mv chrome-headless-shell-mac-arm64 ~/Library/Caches/ms-playwright/chromium_headless_shell-1200/
```

### 方法2：自动安装

```bash
# 如果网络良好，可以让Playwright自动下载
uv run playwright install chromium
uv run playwright install chromium-headless-shell
```

## 使用方法

### 基础用法

```bash
# 自动选择风格生成封面
uv run python scripts/auto_cover_html.py

# 指定输入文件
uv run python scripts/auto_cover_html.py -i output/analyses.json

# 指定输出目录
uv run python scripts/auto_cover_html.py -o output/my_covers
```

### 指定风格

```bash
# 瑞士国际风格（适合技术类）
uv run python scripts/auto_cover_html.py -s swiss

# 科技蓝风格（适合科技类）
uv run python scripts/auto_cover_html.py -s tech

# 极客黑风格（适合编程类）
uv run python scripts/auto_cover_html.py -s geek
```

## 支持的风格

| 风格代码 | 风格名称 | 适用场景 |
|---------|---------|---------|
| `swiss` | 🇨🇭 瑞士国际 | 技术、工具、开发、AI、编程 |
| `acid` | 💚 故障酸性 | 设计、创意、艺术、潮流 |
| `pop` | 🎨 波普撞色 | 新闻、热点、娱乐 |
| `shock` | ⚡️ 冲击波 | 警告、重要、必看 |
| `diffuse` | 🌈 弥散光 | 生活、健康、情感、故事 |
| `sticker` | 🍭 贴纸风 | 可爱、轻松、小技巧 |
| `journal` | 📝 手账感 | 日记、记录、思考、感悟 |
| `cinema` | 🎬 电影感 | 深度、电影、故事、专题 |
| `tech` | 🔵 科技蓝 | 科技、数据、分析、报告 |
| `minimal` | ⚪️ 极简白 | 极简、设计、美学 |
| `memo` | 🟡 备忘录 | 笔记、清单、总结 |
| `geek` | 🟢 极客黑 | 代码、黑客、极客 |

## 字体大小自动调整

脚本根据标题字数自动调整字体大小：

| 标题字数 | 字体大小 |
|---------|---------|
| ≤ 8字   | 140px   |
| 9-12字  | 120px   |
| 13-16字 | 100px   |
| 17-20字 | 85px    |
| 21-25字 | 70px    |
| > 25字  | 55px    |

## 输入数据格式

读取 `output/analyses.json`，格式如下：

```json
[
  {
    "url": "文章URL",
    "title": "文章标题",
    "summary": "文章摘要",
    "categories": ["分类1", "分类2"],
    "score": 20,
    "sender": "发送者",
    "created_at": 1769321529127
  }
]
```

## 输出结果

- **尺寸**：1800×1200 (3:2比例)
- **格式**：PNG
- **命名**：`cover_{风格}_{文章ID}.png`
- **位置**：默认 `output/covers/`

示例：`cover_swiss_ad259bc3.png`

## 工作原理

1. 启动Chromium浏览器（无头模式）
2. 加载CoverMaster.html
3. 根据标题自动选择风格
4. 自动计算并设置字体大小
5. 填充标题和副标题
6. 截取画布区域保存为PNG

## 故障排除

### 问题1：找不到浏览器

```
Error: Executable doesn't exist at /Users/puppet/Library/Caches/ms-playwright/...
```

**解决**：手动下载并安装浏览器（见依赖安装部分）

### 问题2：选择器超时

```
Timeout 30000ms exceeded
```

**解决**：
- 确保CoverMaster.html在项目根目录
- 检查HTML文件是否完整
- 尝试增加等待时间

### 问题3：中文字体显示问题

**解决**：HTML使用Google Fonts加载中文字体，需要网络连接。离线环境需修改HTML引用本地字体。

## 与Pillow版本对比

| 特性 | HTML版本 | Pillow版本 |
|-----|---------|-----------|
| 视觉效果 | ⭐⭐⭐⭐⭐ 完美 | ⭐⭐⭐ 基础 |
| 速度 | ⭐⭐⭐ 较慢（需浏览器） | ⭐⭐⭐⭐⭐ 快速 |
| 依赖 | 需要Playwright+浏览器 | 仅需Pillow |
| 风格一致性 | 100%还原 | 需手动实现 |

**推荐**：
- 如果追求视觉效果 → 使用HTML版本
- 如果需要批量快速生成 → 使用Pillow版本

## 命令行参数

```bash
uv run python scripts/auto_cover_html.py --help

选项:
  -i, --input      输入JSON文件路径 (默认: output/analyses.json)
  -o, --output     输出目录 (默认: output/covers)
  --html           HTML模板文件路径 (默认: CoverMaster.html)
  -s, --style      指定风格 (不指定则自动选择)
  --headless       无头模式运行 (默认: True)
```

## 示例

```bash
# 示例1：批量生成，自动选择风格
uv run python scripts/auto_cover_html.py

# 示例2：技术文章统一用科技蓝风格
uv run python scripts/auto_cover_html.py -s tech

# 示例3：自定义输入输出
uv run python scripts/auto_cover_html.py \
  -i data/articles.json \
  -o output/covers_2025 \
  -s swiss
```

## 技术栈

- **Playwright**：浏览器自动化
- **AsyncIO**：异步执行
- **CoverMaster.html**：封面模板

## 许可

与CoverMaster.html保持一致
