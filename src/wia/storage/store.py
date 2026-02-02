# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""管道输出存储工具。"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from ..core.models import LinkAnalysis, LinkItem, Topic, UserProfile


class JsonStore:
    """将管道输出持久化为 JSON 文件。"""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_links(self, links: Iterable[LinkItem]) -> None:
        self._write_json("links.json", links)

    def write_analyses(self, analyses: Iterable[LinkAnalysis]) -> None:
        self._write_json("analyses.json", analyses)

    def write_topics(self, topics: Iterable[Topic]) -> None:
        self._write_json("topics.json", topics)

    def write_profiles(self, profiles: Iterable[UserProfile]) -> None:
        self._write_json("profiles.json", profiles)

    def _write_json(self, filename: str, items: Iterable) -> None:
        path = self.output_dir / filename
        payload: List[dict] = [asdict(item) for item in items]
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
