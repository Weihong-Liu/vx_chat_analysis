# 微信群聊情报站 (WIA) - 从零到一的实现之路

> 一份关于 vx_chat_analysis 项目起源、架构设计与实现的完整分享

---

## 目录

1. [项目起源：痛点与灵感](#1-项目起源痛点与灵感)
2. [参考项目与借鉴思路](#2-参考项目与借鉴思路)
3. [架构设计：管道模式](#3-架构设计管道模式)
4. [数据模型设计](#4-数据模型设计)
5. [核心模块解析](#5-核心模块解析)
6. [话题聚类算法演进](#6-话题聚类算法演进)
7. [快速开始指南](#7-快速开始指南)
8. [扩展与定制](#8-扩展与定制)

---

## 1. 项目起源：痛点与灵感

### 1.1 问题的发现

微信群聊是我们获取技术资讯、行业动态的重要渠道，但你是否也有这些困扰：

```
每天早上打开群聊：
- 几百条新消息刷屏
- 高价值技术文章被闲聊淹没
- "有人昨天发了那个 AI 工具链接来着？"
- 翻聊天记录翻到手酸
```

**核心痛点**：
- **信息过载**：群消息太多，高价值信息被稀释
- **检索困难**：微信搜索能力弱，找链接像大海捞针
- **缺乏个性化**：没有针对"我关心的技术"做筛选

### 1.2 解决思路

为什么不做一个**知识情报站**？把群聊从"流水账"变成"仪表盘"：

```
传统方式：看聊天记录
        ↓
新方式：看知识仪表盘

核心能力：
1. 自动提取群内所有链接
2. 爬取链接内容，AI 总结摘要
3. 根据你的关键词打分排序
4. 识别话题讨论，聚合相关对话
5. 分析用户画像，谁是"干货王"
```

### 1.3 项目定位

**WeChat Intelligence Agent (WIA)** - 微信群聊知识情报站

- **输入**：微信群聊导出的 JSON 数据
- **输出**：高价值链接、话题摘要、用户画像
- **特点**：离线批处理 → 未来可扩展为实时处理

---

## 2. 参考项目与借鉴思路

### 2.1 MiroFlow Agent - 架构参考

这个项目是 WIA 的"模板"，我们借鉴了它的核心设计思想：

```
MiroFlow Agent (apps/miroflow-agent)
├── MCP 工具层
├── Agent 编排层
└── 应用场景层

WIA (vx_chat_analysis)
├── 工具复用层 (复用 miroflow-tools)
├── 管道编排层 (Pipeline)
└── 分析模块层 (Analysis)
```

**借鉴的关键点**：
1. **管道模式 (Pipeline)**：数据像流水线一样经过多个阶段
2. **工具解耦**：通过 MCP 协议复用工具
3. **可替换设计**：每个处理器都是独立的，可单独替换

### 2.2 MiroFlow Tools - 工具库复用

我们在项目中直接复用了 `libs/miroflow-tools` 工具库：

```python
# WIA 复用的工具
from miroflow_tools import ToolManager

# 复用的具体能力：
- 文档转 Markdown (tool-reading)
- 网页正文抓取 (Jina Reader)
- Google 搜索 (tool-google-search)
```

**复用带来的好处**：
- 不需要重新实现网页抓取
- 工具已通过 MiroThinker 验证，稳定可靠
- 统一的接口规范

### 2.3 其他灵感来源

| 项目 | 借鉴点 |
|------|--------|
| LangChain | Pipeline 思想、工具链抽象 |
| MarkItDown | 文档转 Markdown 的能力 |
| Jina.ai | 网页正文提取 API |
| scikit-learn | TF-IDF 语义相似度计算 |

---

## 3. 架构设计：管道模式

### 3.1 为什么选择管道模式？

```python
# 传统方式（面条式代码）
def analyze_chats(data):
    # 1000 行混杂在一起的代码...
    extract_links(data)
    deduplicate_links(data)
    scrape_links(data)
    # ... 难以维护和测试

# 管道模式（清晰分层）
Pipeline.run(loader):
    stage1: 链接提取
    stage2: 链接过滤
    stage3: 链接去重
    stage4: 内容抓取
    stage5: LLM 分析
    ...
```

**优势**：
1. **可扩展**：添加新阶段不影响现有代码
2. **可测试**：每个阶段可单独测试
3. **可配置**：跳过某些阶段（如 `enable_cleaning=False`）
4. **从离线到实时**：只需替换数据加载层

### 3.2 完整数据流

```
┌─────────────────────────────────────────────────────────────┐
│                      输入：聊天记录 JSON                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段0: 数据清洗 (DataCleaner)                                │
│  - 过滤系统消息                                               │
│  - 过滤群聊通知                                               │
│  - 过滤不支持的内容                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段1: 链接提取 (LinkExtractor)                              │
│  - 正则匹配 URL                                               │
│  - 解析 XML 卡片消息                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段2: 链接过滤 (LinkFilter)                                 │
│  - 过滤重复域名                                               │
│  - 过滤广告/垃圾链接                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段3: 链接去重 (LinkDeduplicator)                           │
│  - 同一 URL 合并                                             │
│  - 记录所有分享者和上下文                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段4: 内容抓取 (LinkScraper)                                │
│  - 使用 Jina Reader 爬取网页正文                              │
│  - 提取标题和内容                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段5: LLM 分析 (LinkSummarizer)                             │
│  - 生成一句话摘要                                              │
│  - 分类（工具/教程/新闻等）                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段6: 关键词评分 (KeywordScorer)                            │
│  - 根据用户关键词打分 0-100                                    │
│  - 给出打分理由                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段7: 话题构建 (TopicBuilder)                               │
│  - 时间窗口聚类                                               │
│  - 引用关系链接                                               │
│  - 语义相似度合并                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段8: 用户画像 (UserProfiler)                               │
│  - 统计发言活跃度                                              │
│  - 计算高价值链接贡献                                         │
│  - 分析关键词倾向                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段9: 存储输出 (JsonStore)                                  │
│  - links.json (原始链接数据)                                  │
│  - analyses.json (分析结果)                                   │
│  - topics.json (话题聚合)                                     │
│  - profiles.json (用户画像)                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段10: 可选 - 飞书发布 (FeishuPublisher)                    │
│  - 生成封面图                                                  │
│  - 发布到飞书多维表格                                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 目录结构

```
vx_chat_analysis/
├── main.py                    # 入口：解析参数，启动管道
├── chat_data/                 # 输入：聊天记录 JSON
├── output/                    # 输出：分析结果
│   ├── links.json
│   ├── analyses.json
│   ├── topics.json
│   └── profiles.json
├── src/wia/
│   ├── core/
│   │   ├── models.py          # 数据模型定义
│   │   ├── pipeline.py        # 管道编排器
│   │   └── stages.py          # 管道阶段定义
│   ├── io/
│   │   ├── chat_loader.py     # 数据加载器
│   │   └── normalizer.py      # 数据标准化
│   ├── analysis/              # 核心分析模块
│   │   ├── data_cleaner.py
│   │   ├── link_extractor.py
│   │   ├── link_filter.py
│   │   ├── deduplicator.py
│   │   ├── scraper.py
│   │   ├── llm_summarizer.py
│   │   ├── keyword_scorer.py
│   │   ├── topic_builder.py
│   │   ├── user_profiler.py
│   │   ├── cover_generator.py
│   │   └── feishu_publisher.py
│   ├── storage/
│   │   └── store.py           # JSON 存储
│   ├── llm/
│   │   ├── base_client.py
│   │   ├── factory.py
│   │   └── providers/
│   │       ├── anthropic_client.py
│   │       └── openai_client.py
│   └── config/
│       └── settings.py
└── libs/miroflow-tools/        # 复用的工具库
```

---

## 4. 数据模型设计

### 4.1 核心数据模型

```python
@dataclass
class ChatMessage:
    """标准化聊天消息"""
    msg_id: str                # 消息唯一 ID
    timestamp: int             # 时间戳
    sender_id: str             # 发送者 ID
    sender_name: str           # 发送者昵称
    msg_type: str              # 消息类型（1=文本, 49=链接卡片）
    content: str               # 消息内容
    xml_content: Optional[str] # XML 卡片数据
    source_file: str           # 来源文件
    type: Optional[str]        # 消息分类（系统消息/文本消息）

@dataclass
class LinkItem:
    """提取的链接"""
    url: str                   # 链接地址
    senders: List[str]         # 分享者列表（去重后可能有多人）
    contexts: List[str]        # 分享时的上下文
    title: Optional[str]       # 标题（从 XML 或爬取）
    description: Optional[str] # 描述（从 XML）
    text: Optional[str]        # 爬取的完整内容
    categories: List[str]      # 类别标签
    created_at: Optional[int]  # 时间戳

@dataclass
class LinkAnalysis:
    """链接分析结果"""
    url: str                   # 链接地址
    title: str                 # 标题
    summary: str               # AI 摘要
    categories: List[str]      # 类型（工具/教程/新闻等）
    score: int                 # 价值评分 0-100
    reason: str                # 打分理由
    sender: Optional[List[str]] # 分享者
    created_at: Optional[int]  # 时间戳
    cover_style: Optional[str] # 封面风格

@dataclass
class Topic:
    """话题聚类结果"""
    topic_id: str              # 话题唯一 ID
    message_ids: List[str]     # 包含的消息 ID
    title: str                 # 话题标题
    participants: List[str]    # 参与者
    initiator: Optional[str]   # 发起人
    start_time: Optional[int]  # 开始时间
    end_time: Optional[int]    # 结束时间
    conclusion: Optional[str]  # 核心结论
    message_count: int         # 消息数量
    messages: List[dict]       # 完整消息内容

@dataclass
class UserProfile:
    """用户画像"""
    user_id: str               # 用户 ID
    user_name: str             # 昵称
    msg_count: int             # 发言总数
    high_value_links: int      # 高价值链接数
    keyword_bias: List[str]    # 关键词倾向
```

### 4.2 设计原则

1. **不可变性**：使用 `@dataclass` (frozen=True)，避免意外修改
2. **可序列化**：所有字段都是 JSON 可序列化的
3. **渐进式增强**：后端计算的字段（如 `score`）与原始数据分离

---

## 5. 核心模块解析

### 5.1 链接提取 (LinkExtractor)

```python
# 从文本和 XML 中提取链接
class LinkExtractor:
    def run(messages: List[ChatMessage]) -> List[LinkItem]:
        # 1. 正则匹配 URL
        # 2. 解析 XML 卡片消息
        # 3. 关联分享者和上下文
```

**实现要点**：
- 使用正则表达式匹配 `https?://[^\s]+`
- 解析微信的 XML 卡片格式
- 提取 `<title>` 和 `<des>` 字段

### 5.2 链接过滤 (LinkFilter)

```python
# 过滤低价值链接
class LinkFilter:
    def run(links: List[LinkItem]) -> List[LinkItem]:
        # 1. 过滤重复域名（如 mp.weixin.qq.com 过多）
        # 2. 过滤广告链接
        # 3. 过滤已知的垃圾链接
```

### 5.3 链接去重 (LinkDeduplicator)

```python
# 同一 URL 合并
class LinkDeduplicator:
    def run(links: List[LinkItem]) -> List[LinkItem]:
        # 1. 按 URL 归一化（去掉 utm_ 参数）
        # 2. 合并相同 URL 的 senders 和 contexts
```

**示例**：
```
输入：
- LinkItem(url="https://example.com", senders=["Alice"])
- LinkItem(url="https://example.com", senders=["Bob"])

输出：
- LinkItem(url="https://example.com", senders=["Alice", "Bob"])
```

### 5.4 内容抓取 (LinkScraper)

```python
# 使用 Jina Reader API 爬取网页
class LinkScraper:
    def run(links: List[LinkItem]) -> List[LinkItem]:
        for link in links:
            # 调用 Jina API
            response = requests.get(f"https://r.jina.ai/{link.url}")
            link.text = response.text
            link.title = extract_title(response.text)
```

**为什么选择 Jina Reader**：
- 无需处理反爬虫
- 自动提取正文，去除广告和导航
- 支持 PDF、视频等特殊格式

### 5.5 LLM 分析 (LinkSummarizer)

```python
# 使用 LLM 生成摘要和分类
class LinkSummarizer:
    PROMPT = """
    请分析以下网页内容，返回 JSON：
    {
        "summary": "一句话摘要（50字以内）",
        "categories": ["工具", "教程", "新闻", "讨论", "其他"],
        "key_points": ["关键点1", "关键点2"]
    }

    网页标题：{title}
    网页内容：{text}
    """
```

### 5.6 关键词评分 (KeywordScorer)

```python
# 根据用户关键词打分
class KeywordScorer:
    def run(analyses: List[LinkAnalysis]) -> List[LinkAnalysis]:
        keywords = ["LLM", "Agent", "Python", "可视化", ...]
        for analysis in analyses:
            # 计算内容与关键词的匹配度
            score = calculate_relevance(analysis, keywords)
            analysis.score = score
```

**评分策略**：
- 标题匹配：+30 分
- 摘要匹配：+20 分
- 正文匹配：+10 分
- 关键词密度：额外加分

### 5.7 话题构建 (TopicBuilder)

这是项目中最复杂的模块，详见下一节。

### 5.8 用户画像 (UserProfiler)

```python
# 统计用户行为
class UserProfiler:
    def run(messages, analyses) -> List[UserProfile]:
        # 1. 按用户聚合消息
        # 2. 计算发言活跃度
        # 3. 统计高价值链接贡献
        # 4. 分析关键词倾向
```

---

## 6. 话题聚类算法演进

### 6.1 V1: 简单时间窗口

```python
# 第一版：最简单的实现
def group_by_time_window(messages, window=300):
    """按 5 分钟时间窗口分组"""
    groups = []
    current_group = [messages[0]]

    for msg in messages[1:]:
        if msg.timestamp - current_group[0].timestamp < window:
            current_group.append(msg)
        else:
            groups.append(current_group)
            current_group = [msg]

    return groups
```

**问题**：
- 无法识别跨时间的长对话
- 同一时间段可能包含多个不相关话题

### 6.2 V2: 添加引用关系检测

```python
# 第二版：利用微信的引用回复功能
def build_reply_chains(messages):
    """构建回复链"""
    chains = {}
    for msg in messages:
        if msg.xml_content:
            # 解析 <refermsg> 标签
            quoted_msg_id = extract_quoted_id(msg.xml_content)
            if quoted_msg_id:
                chains[msg.msg_id] = quoted_msg_id
    return chains

def merge_by_reply_chain(groups, chains):
    """根据引用关系合并话题"""
    # 如果消息 A 引用了消息 B，即使间隔很久也合并到同一话题
```

**XML 格式示例**：
```xml
<msg>
    <refermsg>
        <svrid>7425774398281688365</svrid>
        <displayname>张三</displayname>
        <content>原文内容</content>
    </refermsg>
</msg>
```

### 6.3 V3: 添加语义相似度

```python
# 第三版：使用 TF-IDF 计算相似度
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def merge_similar_groups(groups, threshold=0.3):
    """合并语义相似的话题"""
    texts = [extract_text(g) for g in groups]

    # 计算 TF-IDF 向量
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    # 计算余弦相似度
    similarities = cosine_similarity(tfidf_matrix)

    # 合并相似度 > threshold 的组
    ...
```

### 6.4 V4: 动态时间窗口

```python
# 第四版：根据消息密度调整窗口
def adaptive_time_window(messages):
    """动态调整时间窗口"""
    density = len(messages) / (messages[-1].timestamp - messages[0].timestamp)

    if density > 0.5:      # 高密度
        return 150  # 2.5 分钟
    elif density > 0.2:    # 中密度
        return 300  # 5 分钟
    else:                  # 低密度
        return 600  # 10 分钟
```

### 6.5 完整混合方法

当前版本使用了所有技术：

```python
class TopicBuilder:
    def __init__(
        self,
        time_window=300,              # 基础时间窗口
        min_messages=2,               # 最少消息数
        semantic_threshold=0.3,       # 语义相似度阈值
        enable_reply_chain=True,      # 启用引用检测
        enable_semantic=True,         # 启用语义相似度
        enable_adaptive_window=True,  # 启用动态窗口
    ):
        ...
```

**流程**：
```
阶段1: 时间窗口粗分
    └─ 5分钟窗口初步分组

阶段2: 引用关系链接
    └─ 根据回复关系合并/分割

阶段3: 语义相似度细化
    └─ 计算组间相似度，合并相关话题

阶段4: 质量过滤
    └─ 过滤单条消息或无意义话题
```

---

## 7. 快速开始指南

### 7.1 安装依赖

```bash
cd vx_chat_analysis
uv sync
```

### 7.2 准备数据

将微信群聊导出的 JSON 文件放入 `chat_data/` 目录：

```bash
chat_data/
├── 2025-01-27.json
└── 2025-01-28.json
```

### 7.3 配置环境变量

创建 `.env` 文件：

```bash
# LLM 配置（必需）
ANTHROPIC_API_KEY=your_key_here
# 或使用 OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Jina Reader（必需）
JINA_API_KEY=your_jina_key

# 飞书发布（可选）
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_BITABLE_ID=your_bitable_id
```

### 7.4 运行分析

```bash
# 基础运行
uv run python main.py

# 启用飞书发布
uv run python main.py --enable-feishu

# 自定义输入/输出目录
uv run python main.py --input-dir path/to/chats --output-dir path/to/output
```

### 7.5 查看结果

```bash
output/
├── analyses.json    # 链接分析结果（核心）
├── links.json       # 原始链接数据
├── topics.json      # 话题聚合
├── profiles.json    # 用户画像
└── run.log          # 运行日志
```

### 7.6 可视化展示

使用附带的可视化工具：

```bash
# 启动 Web 展示
cd viewer
python -m http.server 8000
# 访问 http://localhost:8000/topic_viewer.html
```

---

## 8. 扩展与定制

### 8.1 添加自定义关键词

编辑 `src/wia/config/settings.py`：

```python
DEFAULT_KEYWORDS = [
    "LLM", "Agent", "Python",
    "你的关键词1", "你的关键词2"
]
```

### 8.2 添加新的分析阶段

```python
# 1. 创建新模块 src/wia/analysis/my_analyzer.py

class MyAnalyzer:
    def run(self, data):
        # 你的分析逻辑
        return result

# 2. 在 pipeline.py 中集成
from ..analysis.my_analyzer import MyAnalyzer

class Pipeline:
    def __init__(self, ...):
        self.my_analyzer = MyAnalyzer()

    def run(self, loader):
        ...
        # 添加你的阶段
        result = self.my_analyzer.run(data)
```

### 8.3 替换 LLM Provider

```python
# 使用 OpenAI
from src.wia.llm.factory import create_llm_client

llm = create_llm_client(
    provider="openai",
    model="gpt-4o",
    api_key="your_key"
)
```

### 8.4 从离线到实时

```python
# 创建实时数据加载器
class StreamLoader:
    """WebSocket 实时数据加载器"""
    def __init__(self, ws_url):
        self.ws_url = ws_url

    async def load(self):
        async with websockets.connect(self.ws_url) as ws:
            async for message in ws:
                yield ChatMessage.parse_raw(message)

# 在 pipeline 中使用
pipeline.run(StreamLoader(ws_url="ws://localhost:8080"))
```

---

## 总结

WIA 项目从一个简单的"群聊链接提取"想法，演变成了一个完整的知识情报分析系统。它的核心设计理念是：

1. **管道模式**：清晰的分层，易于扩展
2. **工具复用**：站在巨人的肩膀上（miroflow-tools）
3. **渐进增强**：从简单到复杂，逐步优化算法
4. **可配置性**：每个环节都可开关或调整

希望这份文档能帮助你理解项目的设计思路，并激发你的灵感！

---

## 附录：参考资源

- **MiroFlow Agent**: 同仓库下的 `apps/miroflow-agent`
- **MiroFlow Tools**: `libs/miroflow-tools/README.md`
- **Pipeline 设计模式**: https://refactoring.guru/design-patterns/pipeline
- **Jina Reader**: https://jina.ai/reader
- **scikit-learn**: https://scikit-learn.org/

---

*文档版本：v1.0*
*最后更新：2025-01-31*
