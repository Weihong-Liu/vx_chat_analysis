# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""用户画像（基础统计）。"""

from collections import defaultdict
from typing import Dict, Iterable, List

from ..core.models import ChatMessage, LinkAnalysis, UserProfile


class UserProfiler:
    """计算基础用户活跃度统计。"""

    def run(
        self, messages: Iterable[ChatMessage], analyses: Iterable[LinkAnalysis]
    ) -> List[UserProfile]:
        counts: Dict[str, int] = defaultdict(int)
        name_map: Dict[str, str] = {}
        for msg in messages:
            counts[msg.sender_id] += 1
            if msg.sender_id not in name_map:
                name_map[msg.sender_id] = msg.sender_name

        high_value_links = sum(1 for item in analyses if item.score >= 80)

        profiles: List[UserProfile] = []
        for sender_id, msg_count in counts.items():
            profiles.append(
                UserProfile(
                    user_id=sender_id,
                    user_name=name_map.get(sender_id, sender_id),
                    msg_count=msg_count,
                    high_value_links=high_value_links,
                    keyword_bias=[],
                )
            )
        return profiles
