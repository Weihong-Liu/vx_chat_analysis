# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
WIA 运行时配置。

集中管理环境变量与常用路径。
"""


import os
from dotenv import load_dotenv
# 1. 加载 .env 文件中的变量
load_dotenv()
from pathlib import Path

# 基础目录
PROJECT_ROOT = Path("vx_chat_analysis")
CHAT_DATA_DIR = PROJECT_ROOT / "chat_data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 外部工具（可选）
JINA_API_KEY = os.environ.get("JINA_API_KEY")
JINA_BASE_URL = os.environ.get("JINA_BASE_URL", "https://r.jina.ai")

# LLM 配置
# 支持的提供商: anthropic, openai
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "claude-3-5-sonnet-20241022")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "2000"))

# 关键词匹配
KEYWORDS = [kw.strip() for kw in os.environ.get("WIA_KEYWORDS", "").split(",") if kw.strip()]


# 飞书
FEISHU_BASE_URL = os.environ.get("FEISHU_BASE_URL")
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET")