# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""将微信导出 JSON 归一化为 ChatMessage 对象。"""

import re
from typing import Any, Dict, Iterable, List, Optional, Union
from xml.sax.saxutils import escape
from xml.etree import ElementTree as ET

from ..core.models import ChatMessage


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value)


def _extract_xml_content(message: Dict[str, Any]) -> str:
    """
    提取 XML 内容，用于链接提取等场景。

    优先级：
    1. rawContent - 微信实时流格式的原始 XML
    2. source - 导出格式的 msgsource
    """
    # 优先使用 rawContent（包含完整的 XML，包括链接信息）
    raw_content = message.get("rawContent") or ""
    if raw_content and ("<msg>" in raw_content or "<appmsg>" in raw_content):
        return raw_content

    # 降级使用 source 字段（导出格式）
    source = message.get("source") or ""
    if source.startswith("<msgsource>") or "<msgsource>" in source:
        return source

    return ""


def _extract_recordinfo_root(xml_text: str) -> Optional[ET.Element]:
    if not xml_text:
        return None

    match = re.search(r"<recorditem><!\[CDATA\[(.*)\]\]></recorditem>", xml_text, re.S)
    if match:
        try:
            return ET.fromstring(match.group(1))
        except ET.ParseError:
            return None

    # 兼容去除 CDATA 后的 XML 直接解析
    if "<recorditem>" in xml_text:
        sanitized = re.sub(r"<recorditem><!\[CDATA\[", "<recorditem>", xml_text)
        sanitized = re.sub(r"\]\]></recorditem>", "</recorditem>", sanitized)
        try:
            root = ET.fromstring(sanitized)
        except ET.ParseError:
            return None

        recordinfo = root.find(".//recordinfo")
        if recordinfo is not None:
            return recordinfo

    return None


def _build_record_item_content(item: ET.Element, datatype: str) -> str:
    text = _safe_str(
        item.findtext("datadesc")
        or item.findtext("datatitle")
        or item.findtext("title")
    ).strip()
    url = _safe_str(item.findtext("streamweburl")).strip()

    if datatype == "5":
        if text and url:
            return f"{text} {url}"
        if url:
            return url

    if text:
        return text

    if datatype == "2":
        return "[图片]"

    return "[记录消息]"


def _build_record_item_xml_metadata(item: ET.Element) -> str:
    title = _safe_str(item.findtext("datatitle") or item.findtext("title")).strip()
    description = _safe_str(item.findtext("datadesc") or item.findtext("desc")).strip()
    url = _safe_str(item.findtext("streamweburl")).strip()

    if not (title or description or url):
        return ""

    return (
        "<appmsg>"
        f"<title>{escape(title)}</title>"
        f"<des>{escape(description)}</des>"
        f"<url>{escape(url)}</url>"
        "</appmsg>"
    )


def _parse_record_messages(message: Dict[str, Any], source_file: str) -> List[ChatMessage]:
    content = _safe_str(message.get("content") or message.get("parsedContent"))
    raw_content = _safe_str(message.get("rawContent"))
    xml_source = content if "<recorditem>" in content else raw_content
    recordinfo_root = _extract_recordinfo_root(xml_source)
    if recordinfo_root is None:
        return []

    title = _safe_str(recordinfo_root.findtext("title"))
    if not title.endswith("的聊天记录"):
        return []

    datalist = recordinfo_root.find("datalist")
    if datalist is None:
        return []

    base_msg_id = _safe_str(message.get("localId") or message.get("msg_id"))
    base_timestamp = int(message.get("createTime") or message.get("timestamp") or 0)
    record_messages: List[ChatMessage] = []

    for item in datalist.findall("dataitem"):
        data_id = _safe_str(item.findtext("srcMsgLocalid") or item.get("dataid") or item.get("htmlid"))
        msg_id = data_id or base_msg_id
        if base_msg_id and msg_id and base_msg_id not in msg_id:
            msg_id = f"{base_msg_id}:{msg_id}"

        timestamp = int(item.findtext("srcMsgCreateTime") or base_timestamp or 0)
        sender_id = _safe_str(item.findtext("dataitemsource/hashusername"))
        sender_name = _safe_str(item.findtext("sourcename"))
        datatype = _safe_str(item.get("datatype"))
        content = _build_record_item_content(item, datatype)
        xml_metadata = None
        if datatype == "5" and "mp.weixin.qq.com" in _safe_str(item.findtext("streamweburl")):
            xml_metadata = _build_record_item_xml_metadata(item) or None

        record_messages.append(
            ChatMessage(
                msg_id=msg_id,
                timestamp=timestamp,
                sender_id=sender_id,
                sender_name=sender_name,
                msg_type=datatype,
                content=content,
                xml_content=xml_metadata,
                source_file=source_file,
                type="聊天记录",
            )
        )

    return record_messages


def normalize_chat_file(raw: Union[Dict[str, Any], List[Dict[str, Any]]], source_file: str) -> List[ChatMessage]:
    # 兼容两种格式：
    # 1. 导出格式：{"messages": [...]}
    # 2. 实时流格式：直接是数组 [...]
    if isinstance(raw, list):
        messages = raw
    else:
        messages = raw.get("messages", [])

    normalized: List[ChatMessage] = []

    for item in messages:
        record_messages = _parse_record_messages(item, source_file)
        if record_messages:
            normalized.extend(record_messages)
            continue

        msg_id = _safe_str(item.get("localId") or item.get("msg_id"))
        timestamp = int(item.get("createTime") or item.get("timestamp") or 0)
        sender_id = _safe_str(item.get("senderUsername") or item.get("sender_id"))
        sender_name = _safe_str(item.get("senderDisplayName") or item.get("sender_name"))
        msg_type = _safe_str(item.get("localType") or item.get("msg_type") or item.get("type"))
        # 兼容 content 和 parsedContent 两种字段名
        content = _safe_str(item.get("content") or item.get("parsedContent"))
        xml_content = _extract_xml_content(item)

        normalized.append(
            ChatMessage(
                msg_id=msg_id,
                timestamp=timestamp,
                sender_id=sender_id,
                sender_name=sender_name,
                msg_type=msg_type,
                content=content,
                xml_content=xml_content or None,
                source_file=source_file,
                type=item.get("type"),  # 保存消息类型
            )
        )

    return normalized


def main() -> None:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Test chat record normalization")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("chat_data/怎么用AI辅助编程？(2).json"),
        help="Path to chat JSON file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of messages to preview",
    )
    args = parser.parse_args()

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    messages = normalize_chat_file(raw, source_file=str(args.input))

    print(f"normalized messages: {len(messages)}")
    for msg in messages[: args.limit]:
        print(
            f"- id={msg.msg_id} time={msg.timestamp} sender={msg.sender_name} "
            f"msg_type={msg.msg_type} type={msg.type} content={msg.content[:120]} xml_content={msg.xml_content}"
        )


if __name__ == "__main__":
    main()
    