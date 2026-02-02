# 链接卡片功能说明

## 功能概述

现在话题查看器支持解析微信消息中的链接分享，并渲染成漂亮的超链接卡片！

---

## 效果预览

### 消息中的链接卡片

```
┌─────────────────────────────────────┐
│ 👤 张三                1月15日 14:30│
│                                     │
│ 分享一篇文章给大家                   │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Claude Code 升级：Tasks取代Todos│ │ ← 标题
│ │ https://github.com/...          │ │ ← URL
│ ├─────────────────────────────────┤ │
│ │ 最好、最快的内容，总在赛博禅心  │ │ ← 描述
│ ├─────────────────────────────────┤ │
│ │ 🔗 点击打开链接                 │ │ ← 提示
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 交互效果

- **悬停**: 卡片边框变绿，轻微上浮
- **点击**: 在新标签页打开链接

---

## 实现细节

### 1. 后端解析 (`topic_builder.py`)

从微信 XML 中提取链接信息：

```python
def _extract_link_info(self, msg: ChatMessage) -> Optional[dict]:
    """解析 <appmsg> 中的链接"""
    # 提取字段：
    # - title: 链接标题
    # - description: 链接描述
    # - url: 链接地址
```

### 2. 数据结构

每个消息对象新增 `link` 字段：

```json
{
  "msg_id": "7783",
  "sender_name": "张三",
  "content": "分享一篇文章给大家",
  "timestamp": 1706140800,
  "link": {
    "title": "Claude Code 升级：Tasks取代Todos",
    "description": "最好、最快的内容，总在赛博禅心",
    "url": "https://mp.weixin.qq.com/s?__biz=..."
  }
}
```

### 3. 前端渲染 (`topic_viewer.html`)

```html
<a href="${linkUrl}" target="_blank" class="link-card">
  <div class="link-card-header">
    <div class="link-card-title">${linkTitle}</div>
    <div class="link-card-url">${linkUrl}</div>
  </div>
  <div class="link-card-body">
    <div class="link-card-desc">${linkDesc}</div>
  </div>
  <div class="link-card-footer">🔗 点击打开链接</div>
</a>
```

---

## 样式特点

### 视觉设计

- **边框**: 浅灰色边框，悬停时变绿
- **背景**: 纯白色，突出内容
- **层次**: 头部/内容/底部三部分
- **圆角**: 8px 圆角，现代感

### 响应式

- 自动适配容器宽度
- URL 过长时显示省略号
- 描述最多显示 2 行

---

## 使用方法

### 1. 重新运行管道

需要重新运行分析以提取链接信息：

```bash
python main.py
```

### 2. 打开查看器

```bash
open viewer/topic_viewer.html
```

### 3. 查看链接卡片

导入 `topics.json`，点击有链接的话题，就能看到漂亮的卡片！

---

## 支持的链接类型

✅ **微信公众号文章**
✅ **网页链接**
✅ **GitHub 仓库**
✅ **博客文章**
✅ **所有包含 `<appmsg>` 的分享消息**

---

## 技术细节

### XML 解析

支持两种方式提取链接：

1. **XML 解析器** - 使用 `ElementTree`
2. **正则表达式** - 备用方案

### 微信链接格式

```xml
<appmsg>
    <title>链接标题</title>
    <des>链接描述</des>
    <type>5</type>
    <url>https://...</url>
</appmsg>
```

### 错误处理

- 解析失败时静默跳过
- 不影响其他消息显示
- 详细的调试日志

---

## 自定义

### 修改颜色

编辑 HTML 中的 CSS：

```css
.link-card:hover {
    border-color: #4CAF50;  /* 改成你喜欢的颜色 */
}
```

### 修改样式

```css
.link-card {
    border-radius: 12px;  /* 更圆的圆角 */
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);  /* 阴影 */
}
```

---

## 对比

### 之前

```
张三: 分享一篇文章给大家
https://mp.weixin.qq.com/s?__biz=...
```

### 现在

```
┌───────────────────────────────────┐
│ 👤 张三                           │
│                                   │
│ 分享一篇文章给大家                 │
│                                   │
│ ┌─────────────────────────────┐   │
│ │ Claude Code 升级...        │   │
│ │ https://mp.weixin.qq.com/... │   │
│ ├─────────────────────────────┤   │
│ │ 最好、最快的内容...         │   │
│ │ 🔗 点击打开链接             │   │
│ └─────────────────────────────┘   │
└───────────────────────────────────┘
```

清晰、美观、易用！
