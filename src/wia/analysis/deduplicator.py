# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""对批次内链接去重。"""

from typing import Dict, Iterable, List, Optional
from urllib.parse import parse_qs, urlparse

from ..core.models import LinkItem


def _normalize_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    wechat_key = _wechat_sn_key(normalized)
    return wechat_key or normalized


def _wechat_sn_key(url: str) -> Optional[str]:
    if "mp.weixin.qq.com" not in url:
        return None

    parsed = urlparse(url)
    if not parsed.netloc:
        parsed = urlparse(f"https://{url}")

    if not parsed.netloc.endswith("mp.weixin.qq.com"):
        return None
    if not parsed.path.startswith("/s"):
        return None

    sn_values = parse_qs(parsed.query).get("sn")
    if not sn_values:
        return None

    sn = sn_values[0].strip()
    if not sn:
        return None

    return f"mp.weixin.qq.com/s?sn={sn}"


class LinkDeduplicator:
    """合并重复链接并聚合发送者与上下文。"""

    def run(self, links: Iterable[LinkItem]) -> List[LinkItem]:
        merged: Dict[str, LinkItem] = {}

        for link in links:
            key = _normalize_url(link.url)
            if key not in merged:
                merged[key] = link
                continue

            existing = merged[key]
            if not link.senders[0] in existing.senders:
                existing.senders.extend(link.senders)
            existing.contexts.extend(link.contexts)

        return list(merged.values())
