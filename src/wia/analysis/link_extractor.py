# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""从聊天消息中提取链接。"""

import logging
import re
from typing import Iterable, List, Optional

from ..core.models import ChatMessage, LinkItem

logger = logging.getLogger(__name__)
_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")


def _extract_xml_metadata(xml_content: str) -> Optional[dict]:
    """
    从微信XML中提取链接元数据（标题、描述、URL）。

    用于爬取失败时的兜底策略。
    """
    if not xml_content:
        return None

    # 检查是否包含微信链接分享的特征
    if "<title>" not in xml_content and "<appmsg" not in xml_content:
        return None

    # 优先使用正则表达式提取（更稳定，不受XML声明影响）
    title_match = re.search(r"<title>\s*([^<]+?)\s*</title>", xml_content)
    des_match = re.search(r"<des>\s*([^<]+?)\s*</des>", xml_content)
    url_match = re.search(r"<url>\s*([^<]+?)\s*</url>", xml_content)

    metadata = {}
    if title_match:
        metadata["title"] = title_match.group(1).strip()
    if des_match:
        metadata["description"] = des_match.group(1).strip()
    if url_match:
        url = url_match.group(1).strip()
        url = url.replace("&amp;", "&")
        url = url.replace("&lt;", "<")
        url = url.replace("&gt;", ">")
        url = url.replace("&quot;", '"')
        metadata["url"] = url

    if metadata:
        logger.debug(f"从XML提取元数据: {metadata}")
        return metadata

    return None


class LinkExtractor:
    """从文本与 XML 内容中提取 URL。"""

    def run(self, messages: Iterable[ChatMessage]) -> List[LinkItem]:
        links: List[LinkItem] = []

        for message in messages:
            # 提取XML元数据（用于兜底）
            xml_metadata = None
            xml_sources = []

            # 从 xml_content 字段提取
            if message.xml_content:
                xml_sources.append(message.xml_content)

            # 从 content 字段提取（如果包含XML）
            if message.content and ("<appmsg" in message.content or "<title>" in message.content):
                xml_sources.append(message.content)

            # 尝试从所有XML源提取元数据
            for xml_source in xml_sources:
                metadata = _extract_xml_metadata(xml_source)
                if metadata:
                    xml_metadata = metadata
                    break

            candidates = []
            if message.content:
                candidates.extend(_URL_PATTERN.findall(message.content))
            if message.xml_content:
                candidates.extend(_URL_PATTERN.findall(message.xml_content))

            # 使用XML中的URL（如果有的话）
            if xml_metadata and "url" in xml_metadata:
                candidates = [xml_metadata["url"]]

            for url in candidates:
                # 解码URL中的HTML实体
                url = url.replace("&amp;", "&")

                # 创建LinkItem，包含XML元数据
                link_item = LinkItem(
                    url=url,
                    senders=[message.sender_name],
                    contexts=[message.content],
                    xml_metadata=xml_metadata,  # 保存XML元数据作为兜底
                    created_at=message.timestamp * 1000,
                )

                # 如果XML中有标题和描述，预先填充
                if xml_metadata:
                    if "title" in xml_metadata:
                        link_item.title = xml_metadata["title"]
                    if "description" in xml_metadata:
                        link_item.description = xml_metadata["description"]
                        
                links.append(link_item)

        return links
