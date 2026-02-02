# We-ChatRoom Intelligence Agent (WIA)

基于微信社群聊天记录的知识情报分析工具，提供清洗、主题聚合、关键词抽取、用户画像、链接整理、摘要与飞书发布等能力。

- 需求说明见 [PRD.md](PRD.md)

## 功能概览

- 离线批处理管道：从聊天记录生成多维分析结果
- 话题聚合与摘要：输出主题、关键词、重点链接与讨论摘要
- 话题可视化查看器：浏览话题聚类与关联内容
- 用户画像：生成活跃用户特征与兴趣侧写
- 飞书发布：可选将结果同步到飞书多维表格
- 可扩展 Pipeline：模块化分析阶段，便于二次开发

## 环境要求

- Python 3.12+
- macOS / Linux / Windows

## 快速开始

1) 准备聊天记录：

使用 [WeFlow](https://github.com/hicccc77/WeFlow) 导出 JSON 格式记录，放入 [chat_data/](chat_data/) 目录。

2) 安装依赖（任选其一）：

- 使用 uv
    ```bash
    uv sync
    ```
- 使用 pip
    ```bash
    pip install -e .
    ```

3) 配置环境变量（可选）：

在项目根目录创建 [.env](.env) 文件（可参考 [.env.example](.env.example)），常用字段如下：

```bash
JINA_API_KEY=
LLM_PROVIDER=
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL_NAME=
WIA_KEYWORDS=

# 飞书
## 多维表格分享链接，需要设置编辑权限
FEISHU_BASE_URL = ""
## 飞书应用的 App ID 和 App Secret  https://open.feishu.cn/app/
FEISHU_APP_ID = ""
FEISHU_APP_SECRET = ""
```

字段说明可参考 [src/wia/config/settings.py](src/wia/config/settings.py)。

4) 运行分析：

```bash
uv run python main.py --input-dir chat_data --output-dir output
```

如需发布到飞书：

```bash
uv run python main.py --input-dir chat_data --output-dir output --enable-feishu
```

## 输出说明

默认输出到 [output/](output/)：

- [output/analyses.json](output/analyses.json)：综合分析摘要
- [output/topics.json](output/topics.json)：话题聚合结果
- [output/links.json](output/links.json)：链接与引用
- [output/profiles.json](output/profiles.json)：用户画像

按日期归档的历史输出示例见 [output/](output/)。

## 话题可视化查看器使用

1) 确保已生成 [output/topics.json](output/topics.json)。
2) 用浏览器打开 [viewer/topic_viewer.html](viewer/topic_viewer.html)。
3) 点击“导入 JSON 文件”，选择 [output/topics.json](output/topics.json)（或日期目录下的 topics.json）。
4) 即可搜索话题并查看完整对话与摘要。

## 封面生成工具使用

1) 用浏览器打开 [src/wia/tools/CoverMaster2.html](src/wia/tools/CoverMaster2.html)。
2) 在左侧面板填写标题、副标题，选择风格与配色，按需上传图片。
3) 使用代码“下载”生成封面图片（默认 3:2 比例）。具体查看源码。直接下载可能会存在问题。

## 飞书配置

### 多维表格字段配置

请参考 [URL资源橱窗](https://dcn3uptgieg7.feishu.cn/base/IYyBbXXORanUAjsZ6ubcFTZYn8b?from=from_copylink) 项目的字段设置。

字段映射与 `FeishuPublisher._build_fields()` 相关。

### 飞书应用配置

进入 [飞书开放平台](https://open.feishu.cn/app/) 创建应用：

- 获取 `App ID` 与 `App Secret`
- 设置权限管理（批量导入权限）

    ```json
    {
        "scopes": {
            "tenant": [
                "bitable:app",
                "contact:user.employee_id:readonly",
                "contact:user.id:readonly",
                "im:resource"
            ],
            "user": [
                "bitable:app"
            ]
        }
    }
    ```

- 发布应用

## 项目结构

- [main.py](main.py)：管道入口
- [src/wia/](src/wia/)：核心分析模块
- [scripts/](scripts/)：辅助脚本与工具
- [viewer/](viewer/)：话题查看器
- [chat_data/](chat_data/)：输入聊天记录
- [output/](output/)：分析结果输出

## 常见问题

**Q: 没有使用飞书也能运行吗？**

可以。不配置飞书相关环境变量即可，默认不启用飞书发布。

**Q: 如何切换 LLM 提供商？**

设置 `LLM_PROVIDER` 为 `anthropic` 或 `openai`，并提供对应的 `LLM_API_KEY`。

## 致谢

- [WeFlow](https://github.com/hicccc77/WeFlow)：微信聊天记录导出
- [MiroThinker](https://github.com/MiroMindAI/MiroThinker)：参考 [apps/miroflow-agent](https://github.com/MiroMindAI/MiroThinker/tree/main/apps/miroflow-agent) 的结构与编码风格，采用可扩展的 Pipeline 设计
- [Access_wechat_article](https://github.com/yeximm/Access_wechat_article)：微信推文 MCP 参考实现