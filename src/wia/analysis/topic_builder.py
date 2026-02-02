# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""话题重组模块（混合方法）。

识别多条离散消息是否属于同一个讨论串，结合：
1. 时间窗口聚类
2. 引用关系链接
3. 语义相似度细化
4. 质量过滤
"""

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.models import ChatMessage, Topic

logger = logging.getLogger(__name__)


class TopicBuilder:
    """基于混合方法的话题聚类器。"""

    # 配置参数
    DEFAULT_TIME_WINDOW = 300  # 5分钟（秒）
    MIN_MESSAGES_PER_TOPIC = 2  # 最少消息数才能形成话题
    SEMANTIC_SIMILARITY_THRESHOLD = 0.3  # 语义相似度阈值

    def __init__(
        self,
        time_window: int = DEFAULT_TIME_WINDOW,
        min_messages: int = MIN_MESSAGES_PER_TOPIC,
        semantic_threshold: float = SEMANTIC_SIMILARITY_THRESHOLD,
        enable_reply_chain: bool = True,
        enable_semantic: bool = True,
        enable_adaptive_window: bool = True,
    ) -> None:
        """
        初始化话题构建器。

        Args:
            time_window: 基础时间窗口（秒），默认5分钟
            min_messages: 形成话题的最少消息数
            semantic_threshold: 语义相似度阈值（0-1）
            enable_reply_chain: 是否启用引用关系检测
            enable_semantic: 是否启用语义相似度
            enable_adaptive_window: 是否启用动态时间窗口
        """
        self.time_window = time_window
        self.min_messages = min_messages
        self.semantic_threshold = semantic_threshold
        self.enable_reply_chain = enable_reply_chain
        self.enable_semantic = enable_semantic
        self.enable_adaptive_window = enable_adaptive_window

        logger.info(
            f"TopicBuilder initialized: time_window={time_window}s, "
            f"min_messages={min_messages}, semantic_threshold={semantic_threshold}, "
            f"reply_chain={enable_reply_chain}, semantic={enable_semantic}, "
            f"adaptive_window={enable_adaptive_window}"
        )

    def run(self, messages: Iterable[ChatMessage]) -> List[Topic]:
        """
        执行混合话题聚类。

        流程：
        1. 时间窗口粗分
        2. 引用关系链接
        3. 语义相似度细化
        4. 质量过滤

        Args:
            messages: 聊天消息列表

        Returns:
            话题列表
        """
        # 转换为列表并按时间排序
        sorted_messages = sorted(list(messages), key=lambda m: m.timestamp)

        logger.info(f"开始话题聚类，共 {len(sorted_messages)} 条消息")

        if not sorted_messages:
            return []

        # ========== 阶段1: 时间窗口粗分 ==========
        logger.info("阶段1: 时间窗口聚类")
        groups = self._group_by_time_window(sorted_messages)
        logger.info(f"  -> 初步分组: {len(groups)} 个组")

        # ========== 阶段2: 引用关系链接 ==========
        if self.enable_reply_chain:
            logger.info("阶段2: 引用关系链接")
            groups = self._merge_by_reply_relation(groups)
            logger.info(f"  -> 引用合并后: {len(groups)} 个组")

        # ========== 阶段3: 语义相似度细化 ==========
        if self.enable_semantic:
            logger.info("阶段3: 语义相似度细化")
            groups = self._merge_by_semantic_similarity(groups)
            logger.info(f"  -> 语义合并后: {len(groups)} 个组")

        # ========== 阶段4: 质量过滤 ==========
        logger.info("阶段4: 质量过滤")
        groups = [g for g in groups if len(g) >= self.min_messages]
        logger.info(f"  -> 最终话题: {len(groups)} 个（过滤后）")

        # 为每个组创建话题
        topics = [self._create_topic_from_group(group) for group in groups]

        logger.info(f"话题构建完成，共 {len(topics)} 个话题")

        return topics

    # ============================================================
    # 阶段1: 动态时间窗口分组
    # ============================================================

    def _group_by_time_window(self, messages: List[ChatMessage]) -> List[List[ChatMessage]]:
        """
        基于动态时间窗口将消息分组。

        Args:
            messages: 已排序的消息列表

        Returns:
            消息组列表
        """
        if not messages:
            return []

        groups: List[List[ChatMessage]] = []
        current_group: List[ChatMessage] = [messages[0]]

        for i in range(1, len(messages)):
            prev_msg = messages[i - 1]
            curr_msg = messages[i]

            # 计算动态时间窗口
            window = self._get_adaptive_window(current_group)

            # 检查时间差
            time_diff = curr_msg.timestamp - prev_msg.timestamp

            # 如果在时间窗口内，加入当前组
            if time_diff <= window:
                current_group.append(curr_msg)
            else:
                # 超出时间窗口，开始新组
                groups.append(current_group)
                current_group = [curr_msg]

        # 添加最后一组
        if current_group:
            groups.append(current_group)

        return groups

    def _get_adaptive_window(self, current_group: List[ChatMessage]) -> int:
        """
        根据消息密度计算动态时间窗口。

        密集对话 -> 缩短窗口
        稀疏对话 -> 延长窗口

        Args:
            current_group: 当前组的消息

        Returns:
            时间窗口（秒）
        """
        if not self.enable_adaptive_window or len(current_group) < 2:
            return self.time_window

        # 计算当前组的消息密度（条/分钟）
        time_span = current_group[-1].timestamp - current_group[0].timestamp
        if time_span == 0:
            density = len(current_group)
        else:
            density = (len(current_group) / time_span) * 60  # 条/分钟

        # 根据密度调整窗口
        if density > 2:  # 高密度（>2条/分钟）
            return int(self.time_window * 0.5)  # 缩短一半
        elif density > 1:  # 中密度
            return self.time_window
        elif density > 0.5:  # 低密度
            return int(self.time_window * 1.5)  # 延长1.5倍
        else:  # 极低密度
            return int(self.time_window * 2)  # 延长2倍

    # ============================================================
    # 阶段2: 引用关系链接
    # ============================================================

    def _merge_by_reply_relation(self, groups: List[List[ChatMessage]]) -> List[List[ChatMessage]]:
        """
        基于引用关系合并消息组。

        如果消息A引用了消息B，即使它们不在同一个时间窗口内，
        也应该合并到同一个话题中。

        Args:
            groups: 消息组列表

        Returns:
            合并后的消息组列表
        """
        # 构建消息ID到组的映射
        msg_to_group: Dict[str, int] = {}
        for idx, group in enumerate(groups):
            for msg in group:
                msg_to_group[msg.msg_id] = idx

        # 提取所有引用关系
        reply_relations = self._extract_reply_relations(groups)

        if not reply_relations:
            return groups

        logger.info(f"  -> 发现 {len(reply_relations)} 个引用关系")

        # 使用并查集合并组
        parent = list(range(len(groups)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # 根据引用关系合并组
        for reply_msg_id, quoted_msg_id in reply_relations:
            if reply_msg_id in msg_to_group and quoted_msg_id in msg_to_group:
                reply_group_idx = msg_to_group[reply_msg_id]
                quoted_group_idx = msg_to_group[quoted_msg_id]
                union(reply_group_idx, quoted_group_idx)

        # 收集合并后的组
        root_to_messages: Dict[int, List[ChatMessage]] = {}
        for idx, group in enumerate(groups):
            root = find(idx)
            if root not in root_to_messages:
                root_to_messages[root] = []
            root_to_messages[root].extend(group)

        # 按时间重新排序每个组
        merged_groups = []
        for messages in root_to_messages.values():
            sorted_group = sorted(messages, key=lambda m: m.timestamp)
            merged_groups.append(sorted_group)

        return merged_groups

    def _extract_reply_relations(self, groups: List[List[ChatMessage]]) -> List[Tuple[str, str]]:
        """
        提取所有引用关系。

        返回: [(回复消息ID, 被引用消息ID), ...]
        """
        relations = []

        for group in groups:
            # 先构建 msg_id -> message 的映射
            msg_map = {msg.msg_id: msg for msg in group}

            for msg in group:
                quoted_msg_id = self._extract_quoted_msg_id(msg)
                if quoted_msg_id and quoted_msg_id in msg_map:
                    relations.append((msg.msg_id, quoted_msg_id))

        return relations

    def _extract_quoted_msg_id(self, msg: ChatMessage) -> Optional[str]:
        """
        从消息中提取被引用消息的ID。

        微信引用消息格式（在 xml_content 中）：
        <refermsg>
            <svrid>被引用消息的serverId</svrid>
            ...
        </refermsg>
        """
        if not msg.xml_content:
            return None

        try:
            # 方法1: 尝试从 XML 中解析 serverId
            if "<refermsg>" in msg.xml_content:
                root = ET.fromstring(f"<root>{msg.xml_content}</root>")
                refermsg = root.find(".//refermsg")
                if refermsg is not None:
                    svrid = refermsg.find("svrid")
                    if svrid is not None and svrid.text:
                        return f"svrid_{svrid.text}"

            # 方法2: 尝试正则提取 serverId
            pattern = r'<svrid>(\d+)</svrid>'
            match = re.search(pattern, msg.xml_content)
            if match:
                return f"svrid_{match.group(1)}"

        except Exception as e:
            logger.debug(f"Failed to extract quoted msg ID: {e}")

        return None

    # ============================================================
    # 阶段3: 语义相似度细化
    # ============================================================

    def _merge_by_semantic_similarity(self, groups: List[List[ChatMessage]]) -> List[List[ChatMessage]]:
        """
        基于语义相似度合并消息组。

        使用 TF-IDF 计算组的标题/内容的语义相似度，
        合并相似的话题。

        Args:
            groups: 消息组列表

        Returns:
            合并后的消息组列表
        """
        if len(groups) <= 1:
            return groups

        # 提取每个组的代表性文本
        group_texts = [self._get_group_text(group) for group in groups]

        # 计算相似度矩阵
        similarities = self._compute_semantic_similarities(group_texts)

        # 合并相似的组
        merged = [False] * len(groups)
        final_groups: List[List[ChatMessage]] = []

        for i in range(len(groups)):
            if merged[i]:
                continue

            # 找到所有与组i相似的组
            similar_indices = [i]
            for j in range(i + 1, len(groups)):
                if not merged[j] and similarities[i][j] >= self.semantic_threshold:
                    similar_indices.append(j)
                    merged[j] = True

            # 合并所有相似的组
            merged_group = []
            for idx in similar_indices:
                merged_group.extend(groups[idx])
                merged[idx] = True

            # 按时间排序
            merged_group.sort(key=lambda m: m.timestamp)
            final_groups.append(merged_group)

        return final_groups

    def _get_group_text(self, group: List[ChatMessage]) -> str:
        """
        提取消息组的代表性文本。

        使用前3条消息的内容拼接。
        """
        if not group:
            return ""

        # 取前3条消息的内容
        contents = []
        for msg in group[:3]:
            if msg.content and msg.content not in ["[图片]", "[语音]", "[视频]"]:
                contents.append(msg.content)

        return " ".join(contents)

    def _compute_semantic_similarities(self, texts: List[str]) -> np.ndarray:
        """
        计算文本之间的语义相似度矩阵。

        使用 TF-IDF + 余弦相似度。

        Args:
            texts: 文本列表

        Returns:
            相似度矩阵 (n x n)
        """
        # 过滤空文本
        valid_indices = [i for i, text in enumerate(texts) if text.strip()]
        if len(valid_indices) < 2:
            return np.zeros((len(texts), len(texts)))

        valid_texts = [texts[i] for i in valid_indices]

        try:
            # 使用 TF-IDF 向量化
            vectorizer = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 2),
                token_pattern=r"(?u)\b\w+\b",  # 支持中文
            )
            tfidf_matrix = vectorizer.fit_transform(valid_texts)

            # 计算余弦相似度
            similarities = cosine_similarity(tfidf_matrix)

            # 构建完整矩阵
            n = len(texts)
            full_similarities = np.zeros((n, n))
            for i, idx_i in enumerate(valid_indices):
                for j, idx_j in enumerate(valid_indices):
                    full_similarities[idx_i][idx_j] = similarities[i][j]

            return full_similarities

        except Exception as e:
            logger.warning(f"Failed to compute semantic similarities: {e}")
            return np.zeros((len(texts), len(texts)))

    # ============================================================
    # 话题创建
    # ============================================================

    def _create_topic_from_group(self, messages: List[ChatMessage]) -> Topic:
        """
        从消息组创建话题。

        Args:
            messages: 同一组内的消息列表

        Returns:
            话题对象
        """
        # 生成话题ID
        first_msg = messages[0]
        topic_id = self._generate_topic_id(first_msg)

        # 提取基本信息
        message_ids = [m.msg_id for m in messages]
        initiator = first_msg.sender_name
        participants = list(set(m.sender_name for m in messages))
        start_time = messages[0].timestamp
        end_time = messages[-1].timestamp

        # 生成标题和结论
        title = self._generate_title(messages)
        conclusion = self._generate_conclusion(messages)

        # 保存完整的消息内容（用于可视化）
        messages_data = []
        for m in messages:
            # 解析 XML 中的链接信息
            # 优先从 xml_content 获取，如果没有则从 content 获取（可能是原始XML）
            xml_to_parse = m.xml_content if m.xml_content else (m.content if m.content.startswith('<') else None)
            link_info = self._extract_link_info_from_xml(xml_to_parse)

            messages_data.append(
                {
                    "msg_id": m.msg_id,
                    "sender_name": m.sender_name,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "msg_type": m.msg_type,
                    "link": link_info,  # 链接信息（如果有）
                }
            )

        topic = Topic(
            topic_id=topic_id,
            message_ids=message_ids,
            title=title,
            participants=participants,
            initiator=initiator,
            start_time=start_time,
            end_time=end_time,
            conclusion=conclusion,
            message_count=len(messages),
            messages=messages_data,
        )

        return topic

    def _generate_topic_id(self, message: ChatMessage) -> str:
        """生成唯一的话题ID。"""
        content = f"{message.timestamp}_{message.sender_id}_{message.msg_id}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_title(self, messages: List[ChatMessage]) -> str:
        """
        生成话题标题。

        使用第一条有实际内容的消息。
        """
        if not messages:
            return "未知话题"

        # 找第一条有实际内容的消息
        for msg in messages:
            content = msg.content.strip()
            if content and content not in ["[图片]", "[语音]", "[视频]", "[表情]"]:
                title = content.replace("\n", " ")
                title = " ".join(title.split())
                if len(title) > 50:
                    title = title[:50] + "..."
                return title

        return "未知话题"

    def _extract_link_info_from_xml(self, xml_content: Optional[str]) -> Optional[dict]:
        """
        从 XML 内容中提取链接信息。

        微信链接分享消息格式：
        <appmsg>
            <title>链接标题</title>
            <des>链接描述</des>
            <url>https://...</url>
        </appmsg>

        Args:
            xml_content: XML 字符串

        Returns:
            包含 title, description, url 的字典，如果没有链接则返回 None
        """
        if not xml_content:
            return None

        try:
            # 方法1: 使用 XML 解析
            if "<appmsg>" in xml_content:
                root = ET.fromstring(f"<root>{xml_content}</root>")
                appmsg = root.find(".//appmsg")

                if appmsg is not None:
                    title_elem = appmsg.find("title")
                    desc_elem = appmsg.find("des")
                    url_elem = appmsg.find("url")

                    title = title_elem.text if title_elem is not None else None
                    description = desc_elem.text if desc_elem is not None else None
                    url = url_elem.text if url_elem is not None else None

                    if title or url:
                        return {
                            "title": title,
                            "description": description,
                            "url": url,
                        }

            # 方法2: 使用正则表达式提取（备用）
            title_match = re.search(r'<title>([^<]+)</title>', xml_content)
            desc_match = re.search(r'<des>([^<]+)</des>', xml_content)
            url_match = re.search(r'<url>([^<]+)</url>', xml_content)

            title = title_match.group(1) if title_match else None
            description = desc_match.group(1) if desc_match else None
            url = url_match.group(1) if url_match else None

            if title or url:
                return {
                    "title": title,
                    "description": description,
                    "url": url,
                }

        except Exception as e:
            logger.debug(f"Failed to extract link info: {e}")

        return None

    def _generate_conclusion(self, messages: List[ChatMessage]) -> Optional[str]:
        """
        生成话题核心结论。

        汇总关键消息内容。
        """
        if len(messages) <= 1:
            return None

        # 收集有内容的消息
        content_messages = [
            m for m in messages[:5]
            if m.content and m.content.strip() not in ["[图片]", "[语音]", "[视频]"]
        ]

        if not content_messages:
            return None

        # 拼接内容
        contents = [m.content[:100].strip() for m in content_messages]
        conclusion = " | ".join(contents)

        # 限制长度
        if len(conclusion) > 300:
            conclusion = conclusion[:300] + "..."

        return conclusion
