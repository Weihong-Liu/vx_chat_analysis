# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""自定义链接过滤器。"""

from typing import Iterable, List

from ..core.models import LinkItem


class LinkFilter:
    """过滤不需要的链接。"""

    def __init__(self) -> None:
        self.blocked_domains = [
            "support.weixin.qq.com",
            "finder.video.qq.com",
            "bigmodel.cn/glm-coding",
            "dcn3uptgieg7.feishu.cn/base/IYyBbXXORanUAjsZ6ubcFTZYn8b"
        ]
        self.blocked_title_keywords = [
            "Datawhale 2026 日历",
        ]

    def run(self, links: Iterable[LinkItem]) -> List[LinkItem]:
        filtered: List[LinkItem] = []

        for link in links:
            url = link.url or ""
            title = link.title or ""

            if any(domain in url for domain in self.blocked_domains):
                continue

            if any(keyword in title for keyword in self.blocked_title_keywords):
                continue

            filtered.append(link)

        return filtered
