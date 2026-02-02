# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""
WIA 项目入口。

负责组装分析管道并执行离线批处理流程。
"""

import argparse
import logging
import sys
from pathlib import Path

from src.wia.core.pipeline import Pipeline
from src.wia.io.chat_loader import FileLoader

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WIA 离线分析管道")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("chat_data"),
        help="聊天记录 JSON 目录",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="分析结果输出目录",
    )
    parser.add_argument(
        "--enable-feishu",
        action="store_true",
        help="启用飞书发布（需要配置 .env 中的飞书凭证）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.output_dir / "run.log"
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger.handlers = [stream_handler, file_handler]

    loader = FileLoader(input_dir=args.input_dir)
    pipeline = Pipeline(output_dir=args.output_dir, enable_feishu=args.enable_feishu)

    logger.info("开始执行 WIA 管道")
    if args.enable_feishu:
        logger.info("飞书发布已启用")

    try:
        pipeline.run(loader)
        logger.info("WIA 管道执行完成")
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
