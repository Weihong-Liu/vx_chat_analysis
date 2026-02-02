import os
import json
from datetime import datetime

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.drive.v1 import *
from urllib.parse import urlparse


# ======================================================
# 工具函数
# ======================================================
def parse_bitable_app_token(url: str) -> str:
    """
    从飞书多维表格（Base）URL 中解析 app_token

    示例：
    https://xxx.feishu.cn/base/IYyBxxxxxx?from=xxx
    -> IYyBxxxxxx
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    # Base URL 结构：/base/{app_token}
    if "base" not in path_parts:
        raise ValueError("该 URL 不是飞书多维表格（Base）链接")

    base_index = path_parts.index("base")

    try:
        app_token = path_parts[base_index + 1]
    except IndexError:
        raise ValueError("未能从 URL 中解析出 app_token")

    return app_token


def datetime_to_unix_ms(dt: datetime) -> int:
    """datetime -> Unix 时间戳（毫秒）"""
    return int(dt.timestamp() * 1000)


# ======================================================
# Feishu Client 封装
# ======================================================
class FeishuClient:
    def __init__(self, app_id: str, app_secret: str):
        self.client = (
            lark.Client.builder()
            .app_id(app_id)
            .app_secret(app_secret)
            .log_level(lark.LogLevel.DEBUG)
            .build()
        )


# ======================================================
# 文件上传服务（用于封面 / 附件）
# ======================================================
class FeishuFileUploader:
    def __init__(self, feishu_client: FeishuClient):
        self.client = feishu_client.client

    def upload_image_to_bitable(self, file_path: str, app_token: str) -> str:
        """
        上传图片到多维表格，返回 file_token
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        file = open(file_path, "rb")

        request: UploadAllMediaRequest = (
            UploadAllMediaRequest.builder()
            .request_body(
                UploadAllMediaRequestBody.builder()
                .file_name(os.path.basename(file_path))
                .parent_type("bitable_image")
                .parent_node(app_token)
                .size(os.path.getsize(file_path))
                .file(file)
                .build()
            )
            .build()
        )

        response: UploadAllMediaResponse = self.client.drive.v1.media.upload_all(request)

        if not response.success():
            raise RuntimeError(
                f"upload_all failed, code={response.code}, msg={response.msg}, "
                f"log_id={response.get_log_id()}, resp={response.raw.content}"
            )

        return response.data.file_token


# ======================================================
# 多维表格 Base Service（核心）
# ======================================================
class FeishuBaseService:
    def __init__(
        self,
        feishu_client: FeishuClient,
        app_token: str,
        table_id: str | None = None,
        table_name: str | None = None,
        auto_pick_first: bool = True
    ):
        """
        table_id / table_name 都不知道也可以
        默认自动选择第一个表
        """
        self.client = feishu_client.client
        self.app_token = app_token

        if table_id:
            self.table_id = table_id
        elif table_name:
            self.table_id = self.get_table_id_by_name(table_name)
        else:
            tables = self.list_tables()
            if not tables:
                raise RuntimeError("该多维表格下没有任何数据表")

            if not auto_pick_first:
                raise RuntimeError(
                    "未指定 table_id / table_name，请先调用 list_tables() 查看"
                )

            # 默认选第一个表
            self.table_id = tables[0].table_id

    # --------------------------------------------------
    # 列出所有数据表（自动分页）
    # --------------------------------------------------
    def list_tables(self) -> list:
        tables = []
        page_token = None

        while True:
            request = (
                ListAppTableRequest.builder()
                .app_token(self.app_token)
                .page_size(100)
                .build()
            )

            response = self.client.bitable.v1.app_table.list(request)

            if not response.success():
                raise RuntimeError(
                    f"list_tables failed, code={response.code}, msg={response.msg}, "
                    f"log_id={response.get_log_id()}"
                )

            data = response.data
            tables.extend(data.items)

            if not data.has_more:
                break

            page_token = data.page_token

        return tables

    # --------------------------------------------------
    # 按表名查 table_id
    # --------------------------------------------------
    def get_table_id_by_name(self, table_name: str) -> str:
        for table in self.list_tables():
            if table.name == table_name:
                return table.table_id
        raise ValueError(f"未找到数据表: {table_name}")

    # --------------------------------------------------
    # 新增一条记录
    # --------------------------------------------------
    def create_record(self, fields: dict):
        request: CreateAppTableRecordRequest = (
            CreateAppTableRecordRequest.builder()
            .app_token(self.app_token)
            .table_id(self.table_id)
            .ignore_consistency_check(True)
            .request_body(
                AppTableRecord.builder()
                .fields(fields)
                .build()
            )
            .build()
        )

        response: CreateAppTableRecordResponse = (
            self.client.bitable.v1.app_table_record.create(request)
        )

        if not response.success():
            raise RuntimeError(
                f"create_record failed, code={response.code}, msg={response.msg}, "
                f"log_id={response.get_log_id()}, resp={response.raw.content}"
            )

        return response.data


# ======================================================
# main：业务入口示例
# ======================================================
def main():
    from src.wia.config import settings
    # -------------------------
    # 基础配置（替换成你自己的）
    # -------------------------
    APP_ID = settings.FEISHU_APP_ID
    APP_SECRET = settings.FEISHU_APP_SECRET
    URL = settings.FEISHU_BASE_URL

    # Base URL 中的 app_token
    APP_TOKEN = parse_bitable_app_token(URL)

    IMAGE_PATH = "./test.png"

    # -------------------------
    # 初始化 Client
    # -------------------------
    feishu_client = FeishuClient(APP_ID, APP_SECRET)

    # -------------------------
    # 初始化 BaseService（不知道表名也没关系）
    # -------------------------
    base_service = FeishuBaseService(
        feishu_client,
        app_token=APP_TOKEN
    )

    print("当前使用的 table_id:", base_service.table_id)

    # -------------------------
    # 上传封面
    # -------------------------
    uploader = FeishuFileUploader(feishu_client)
    file_token = uploader.upload_image_to_bitable(
        IMAGE_PATH,
        APP_TOKEN
    )

    # -------------------------
    # 构造 fields（严格符合 Base 类型）
    # -------------------------
    fields = {
        "标题": {
            "text": "面向对象封装的 Base 示例",
            "link": "https://open.feishu.cn"
        },
        "简介": "这是一个把所有能力封装到单文件的示例",
        "类型": ["技术文档", "其他"],
        "分享者": "Puppet",
        "创建日期": datetime_to_unix_ms(datetime.now()),
        "封面": [
            {
                "file_token": file_token
            }
        ]
    }

    # -------------------------
    # 写入 Base
    # -------------------------
    record = base_service.create_record(fields)

    lark.logger.info("✅ Record created:")
    lark.logger.info(lark.JSON.marshal(record, indent=4))


if __name__ == "__main__":
    main()