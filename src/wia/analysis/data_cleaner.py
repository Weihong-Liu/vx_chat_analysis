# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""数据清洗模块。

过滤无效消息，提高数据质量。
"""

import logging
from typing import Iterable, List, Optional

from ..core.models import ChatMessage

logger = logging.getLogger(__name__)


class DataCleaner:
    """清洗聊天数据，过滤无效消息。"""

    # 需要过滤的消息类型
    FILTER_TYPES = {"系统消息"}

    # 需要过滤的发送者后缀
    FILTER_SENDER_SUFFIXES = {"@chatroom"}

    # 需要过滤的 XML 内容
    FILTER_XML_PATTERNS = [
        "当前版本不支持展示该内容",
        "请升级至最新版本",
        "版本不支持",
    ]

    def __init__(
        self,
        filter_system_messages: bool = True,
        filter_chatroom_messages: bool = True,
        filter_unsupported_messages: bool = True,
    ) -> None:
        """
        初始化数据清洗器。

        Args:
            filter_system_messages: 是否过滤系统消息
            filter_chatroom_messages: 是否过滤群聊系统消息
            filter_unsupported_messages: 是否过滤不支持的消息
        """
        self.filter_system_messages = filter_system_messages
        self.filter_chatroom_messages = filter_chatroom_messages
        self.filter_unsupported_messages = filter_unsupported_messages

        logger.info(
            f"DataCleaner initialized: "
            f"filter_system={filter_system_messages}, "
            f"filter_chatroom={filter_chatroom_messages}, "
            f"filter_unsupported={filter_unsupported_messages}"
        )

    def run(self, messages: Iterable[ChatMessage]) -> List[ChatMessage]:
        """
        清洗数据，过滤无效消息。

        Args:
            messages: 聊天消息列表

        Returns:
            清洗后的消息列表
        """
        messages_list = list(messages)
        original_count = len(messages_list)

        logger.info(f"开始数据清洗，原始消息数: {original_count}")

        cleaned = []

        # 统计过滤原因
        filter_reasons = {
            "系统消息": 0,
            "群聊消息": 0,
            "不支持内容": 0,
            "保留": 0,
        }

        for msg in messages_list:
            should_filter, reason = self._should_filter(msg)

            if should_filter:
                filter_reasons[reason] += 1
            else:
                cleaned.append(msg)
                filter_reasons["保留"] += 1

        # 输出统计
        logger.info("数据清洗完成:")
        for reason, count in filter_reasons.items():
            if reason != "保留":
                logger.info(f"  - 过滤 {reason}: {count} 条")
        logger.info(f"  - 保留消息: {filter_reasons['保留']} 条")
        logger.info(f"清洗率: {(original_count - len(cleaned)) / original_count * 100:.1f}%")

        return cleaned

    def _should_filter(self, msg: ChatMessage) -> tuple[bool, str]:
        """
        判断消息是否应该被过滤。

        Returns:
            (should_filter, reason): 是否过滤及原因
        """
        # 检查 1: 系统消息类型
        if self.filter_system_messages and self._is_system_message(msg):
            return True, "系统消息"

        # 检查 2: 群聊系统消息
        if self.filter_chatroom_messages and self._is_chatroom_message(msg):
            return True, "群聊消息"

        # 检查 3: 不支持的内容
        if self.filter_unsupported_messages and self._is_unsupported_content(msg):
            return True, "不支持内容"

        # 通过所有检查
        return False, "保留"

    def _is_system_message(self, msg: ChatMessage) -> bool:
        """
        判断是否为系统消息。

        检查 type 字段是否为"系统消息"。
        """
        # 检查 type 字段
        if hasattr(msg, 'type') and msg.type == "系统消息":
            return True

        # 检查常见系统消息关键词
        system_keywords = [
            "邀请你加入了群聊",
            "撤回了一条消息",
            "修改群名为",
            "邀请",
            "移出群聊",
        ]

        content_lower = msg.content.lower() if msg.content else ""
        for keyword in system_keywords:
            if keyword in content_lower:
                return True

        return False

    def _is_chatroom_message(self, msg: ChatMessage) -> bool:
        """
        判断是否为群聊系统消息。

        检查 senderUsername 是否以 @chatroom 结尾。
        """
        sender_id = msg.sender_id if msg.sender_id else ""

        # 检查是否以 @chatroom 结尾
        if sender_id.endswith("@chatroom"):
            # 额外检查：如果只是普通文本消息，可能不是系统消息
            # 但通常 @chatroom 的消息都是群发的系统通知
            return True

        return False

    def _is_unsupported_content(self, msg: ChatMessage) -> bool:
        """
        判断是否包含不支持的内容。

        检查 content 或 xml_content 中是否包含不支持提示。
        """
        # 检查 content 字段
        if msg.content:
            for pattern in self.FILTER_XML_PATTERNS:
                if pattern in msg.content:
                    return True

        # 检查 xml_content 字段
        if msg.xml_content:
            for pattern in self.FILTER_XML_PATTERNS:
                if pattern in msg.xml_content:
                    return True

        return False
