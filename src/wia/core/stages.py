# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""管道阶段接口。"""

from abc import ABC, abstractmethod
from typing import Any


class Stage(ABC):
    """管道阶段基类。"""

    @abstractmethod
    def run(self, data: Any) -> Any:
        """执行当前阶段并返回变换后的数据。"""
        raise NotImplementedError
