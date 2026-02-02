# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""WIA 管道数据模型。"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChatMessage:
    msg_id: str
    timestamp: int
    sender_id: str
    sender_name: str
    msg_type: str
    content: str
    xml_content: Optional[str]
    source_file: str
    type: Optional[str] = None  # 消息类型（系统消息、文本消息等）


@dataclass
class LinkItem:
    url: str
    senders: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)
    title: Optional[str] = None  # 从XML或爬取获取
    description: Optional[str] = None  # 从XML获取的描述
    text: Optional[str] = None  # 爬取的完整文本内容
    xml_metadata: Optional[dict] = None  # 保存XML中提取的元数据（兜底用）
    categories: List[str] = field(default_factory=list)  # 链接类别（支持多选）
    created_at: Optional[int] = None  # 创建时间戳


@dataclass
class LinkAnalysis:
    url: str
    title: str  # 标题
    summary: str  # 简介/摘要
    categories: List[str]  # 类型（支持多选）
    score: int  # 价值评分 0-100
    reason: str  # 打分理由
    sender: Optional[List[str]] = field(default_factory=list)  # 分享者（后续组装）
    created_at: Optional[int] = None  # 创建时间戳（后续组装）
    cover_style: Optional[str] = None  # 封面风格 key


@dataclass
class Topic:
    topic_id: str
    message_ids: List[str]
    title: str
    participants: List[str]
    initiator: Optional[str] = None  # 话题发起人
    start_time: Optional[int] = None  # 话题开始时间戳
    end_time: Optional[int] = None  # 话题结束时间戳
    conclusion: Optional[str] = None  # 核心结论/摘要
    message_count: int = 0  # 消息数量
    messages: List[dict] = field(default_factory=list)  # 完整的消息内容


@dataclass
class UserProfile:
    user_id: str
    user_name: str
    msg_count: int
    high_value_links: int
    keyword_bias: List[str]
