# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""聊天数据加载器。"""

import json
import logging
from pathlib import Path
from typing import List

from ..core.models import ChatMessage
from .normalizer import normalize_chat_file

logger = logging.getLogger(__name__)


class FileLoader:
    """从目录加载聊天记录 JSON 文件。"""

    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir

    def load(self) -> List[ChatMessage]:
        if not self.input_dir.exists():
            raise FileNotFoundError(f"未找到输入目录: {self.input_dir}")

        messages: List[ChatMessage] = []
        for file_path in sorted(self.input_dir.glob("*.json")):
            logger.info("读取文件 %s", file_path)
            with file_path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            messages.extend(normalize_chat_file(raw, source_file=str(file_path)))

        return messages
