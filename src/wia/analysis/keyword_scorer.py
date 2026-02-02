# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""基于关键词的链接评分。"""

from typing import Iterable, List

from ..config.settings import KEYWORDS
from ..core.models import LinkAnalysis


class KeywordScorer:
    """基于关键词匹配计算简单评分。"""

    def __init__(self, keywords: List[str] | None = None) -> None:
        self.keywords = keywords or KEYWORDS

    def run(self, analyses: Iterable[LinkAnalysis]) -> List[LinkAnalysis]:
        scored: List[LinkAnalysis] = []
        for item in analyses:
            if self.keywords:
                hits = sum(1 for kw in self.keywords if kw.lower() in item.summary.lower())
                item.score = min(100, hits * 20)
                if hits > 0:
                    item.reason = f"matched_keywords={hits}"
            scored.append(item)
        return scored
