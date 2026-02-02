# Copyright (c) 2025 MiroMind
# This source code is licensed under the MIT License.

"""发布链接分析结果到飞书多维表格。"""

import logging
from typing import Dict, Iterable, List, Optional

from ..config.settings import (
    FEISHU_APP_ID,
    FEISHU_APP_SECRET,
    FEISHU_BASE_URL,
)
from ..core.models import LinkAnalysis
from ..tools.feishu_base_app import (
    FeishuBaseService,
    FeishuClient,
    FeishuFileUploader,
    parse_bitable_app_token,
)

logger = logging.getLogger(__name__)


class FeishuPublisher:
    """将链接分析结果发布到飞书多维表格。"""

    # 飞书字段映射
    FIELD_MAPPING = {
        "标题": "title",
        "简介": "summary",
        "类型": "categories",
        "分享者": "sender",
        "创建日期": "created_at",
        "封面": "cover",
    }

    def __init__(self, enabled: bool = True):
        """
        初始化飞书发布器。

        Args:
            enabled: 是否启用飞书发布
        """
        self.enabled = enabled and bool(FEISHU_APP_ID and FEISHU_APP_SECRET and FEISHU_BASE_URL)
        self._client: Optional[FeishuClient] = None
        self._base_service: Optional[FeishuBaseService] = None
        self._file_uploader: Optional[FeishuFileUploader] = None

        if self.enabled:
            try:
                self._init_feishu_client()
                logger.info("FeishuPublisher enabled and initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Feishu client, publishing disabled: {e}")
                self.enabled = False
        else:
            logger.info("FeishuPublisher disabled")

    def _init_feishu_client(self) -> None:
        """初始化飞书客户端。"""
        if not FEISHU_APP_ID or not FEISHU_APP_SECRET or not FEISHU_BASE_URL:
            raise ValueError("Feishu credentials not configured")

        # 解析 app_token
        app_token = parse_bitable_app_token(FEISHU_BASE_URL)

        # 初始化客户端
        self._client = FeishuClient(FEISHU_APP_ID, FEISHU_APP_SECRET)

        # 初始化 Base 服务
        self._base_service = FeishuBaseService(self._client, app_token=app_token)
        self._file_uploader = FeishuFileUploader(self._client)

        logger.info(f"Connected to Feishu Base: {FEISHU_BASE_URL}")

    def run(self, analyses: Iterable[LinkAnalysis], cover_map: Optional[Dict[str, str]] = None) -> int:
        """
        发布分析结果到飞书。

        Args:
            analyses: 链接分析列表

        Returns:
            成功发布的记录数
        """
        if not self.enabled:
            logger.info("Feishu publishing disabled, skipping")
            return 0

        analyses_list = list(analyses)
        logger.info(f"Publishing {len(analyses_list)} analyses to Feishu")

        success_count = 0
        for idx, analysis in enumerate(analyses_list, 1):
            try:
                self._publish_single(analysis, cover_map=cover_map or {})
                success_count += 1
                logger.info(f"[{idx}/{len(analyses_list)}] ✓ Published: {analysis.title[:30]}")
            except Exception as e:
                logger.error(f"[{idx}/{len(analyses_list)}] ✗ Failed to publish: {analysis.url}, error: {e}")

        logger.info(f"Published {success_count}/{len(analyses_list)} records to Feishu")
        return success_count

    def _publish_single(self, analysis: LinkAnalysis, cover_map: Dict[str, str]) -> None:
        """发布单条分析记录。"""
        # 构造飞书字段格式
        cover_token = self._upload_cover(analysis, cover_map)
        fields = self._build_fields(analysis, cover_token)

        # 创建记录
        self._base_service.create_record(fields)

    def _build_fields(self, analysis: LinkAnalysis, cover_token: Optional[str]) -> dict:
        """
        将 LinkAnalysis 转换为飞书字段格式。

        飞书字段格式参考：
        {
            "标题": {"text": "标题", "link": "url"},
            "简介": "摘要文本",
            "类型": ["类型1", "类型2"],  # 多选
            "分享者": "分享者名称",
            "创建日期": 1234567890,  # 毫秒时间戳
        }
        """
        fields = {
            "标题": {
                "text": analysis.title or analysis.url[:50],
                "link": analysis.url
            },
            "简介": analysis.summary,
            "类型": analysis.categories or ["其他"],
        }

        # 可选字段
        if analysis.sender:
            fields["分享者"] = analysis.sender

        if analysis.created_at:
            fields["创建日期"] = analysis.created_at

        if cover_token:
            fields["封面"] = [{"file_token": cover_token}]

        return fields

    def _upload_cover(self, analysis: LinkAnalysis, cover_map: Dict[str, str]) -> Optional[str]:
        if not cover_map or not self._file_uploader or not self._base_service:
            return None

        cover_path = cover_map.get(analysis.url)
        if not cover_path:
            return None

        try:
            return self._file_uploader.upload_image_to_bitable(
                cover_path,
                self._base_service.app_token,
            )
        except Exception as exc:
            logger.warning("封面上传失败: %s", exc)
            return None

    def close(self) -> None:
        """关闭连接（当前无需操作，为接口一致性保留）。"""
        pass
