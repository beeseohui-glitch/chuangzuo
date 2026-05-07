"""
COS 工具 - 腾讯云对象存储读写
"""

import os
from typing import Optional

from pydantic import Field, PrivateAttr
from qcloud_cos import CosConfig, CosS3Client

from crewai.tools import BaseTool


def _make_cos_client(secret_id: str, secret_key: str, region: str) -> CosS3Client:
    config = CosConfig(
        Region=region,
        SecretId=secret_id,
        SecretKey=secret_key,
    )
    return CosS3Client(config)


class COSUploadTool(BaseTool):
    """COS 上传工具"""

    name: str = "cos_upload"
    description: str = "上传文件到腾讯云COS对象存储"
    secret_id: str = Field(default_factory=lambda: os.getenv("COS_SECRET_ID", ""))
    secret_key: str = Field(default_factory=lambda: os.getenv("COS_SECRET_KEY", ""))
    region: str = Field(default_factory=lambda: os.getenv("COS_REGION", "ap-guangzhou"))
    bucket: str = Field(default_factory=lambda: os.getenv("COS_BUCKET", ""))

    _client: Optional[CosS3Client] = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        if self.secret_id and self.secret_key:
            self._client = _make_cos_client(self.secret_id, self.secret_key, self.region)

    @property
    def client(self) -> CosS3Client:
        if self._client is None:
            self._client = _make_cos_client(self.secret_id, self.secret_key, self.region)
        return self._client

    def _run(
        self,
        file_path: str,
        cos_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        bucket_name = bucket or self.bucket
        self.client.put_object_from_local_file(
            Bucket=bucket_name,
            LocalFilePath=file_path,
            Key=cos_path,
        )
        return f"https://{bucket_name}.cos.{self.region}.myqcloud.com/{cos_path}"

    def upload_bytes(
        self,
        data: bytes,
        cos_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        bucket_name = bucket or self.bucket
        self.client.put_object(
            Bucket=bucket_name,
            Body=data,
            Key=cos_path,
        )
        return f"https://{bucket_name}.cos.{self.region}.myqcloud.com/{cos_path}"

    def upload_text(
        self,
        text: str,
        cos_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        return self.upload_bytes(text.encode("utf-8"), cos_path, bucket)


class COSDownloadTool(BaseTool):
    """COS 下载工具"""

    name: str = "cos_download"
    description: str = "从腾讯云COS对象存储下载文件"
    secret_id: str = Field(default_factory=lambda: os.getenv("COS_SECRET_ID", ""))
    secret_key: str = Field(default_factory=lambda: os.getenv("COS_SECRET_KEY", ""))
    region: str = Field(default_factory=lambda: os.getenv("COS_REGION", "ap-guangzhou"))
    bucket: str = Field(default_factory=lambda: os.getenv("COS_BUCKET", ""))

    _client: Optional[CosS3Client] = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        if self.secret_id and self.secret_key:
            self._client = _make_cos_client(self.secret_id, self.secret_key, self.region)

    @property
    def client(self) -> CosS3Client:
        if self._client is None:
            self._client = _make_cos_client(self.secret_id, self.secret_key, self.region)
        return self._client

    def _run(
        self,
        cos_path: str,
        local_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        bucket_name = bucket or self.bucket
        self.client.get_object(
            Bucket=bucket_name,
            Key=cos_path,
            DestPath=local_path,
        )
        return local_path

    def download_bytes(self, cos_path: str, bucket: Optional[str] = None) -> bytes:
        bucket_name = bucket or self.bucket
        response = self.client.get_object(
            Bucket=bucket_name,
            Key=cos_path,
        )
        return response["Body"].get_raw_stream().read()

    def download_text(self, cos_path: str, bucket: Optional[str] = None) -> str:
        return self.download_bytes(cos_path, bucket).decode("utf-8")


class COSDeleteTool(BaseTool):
    """COS 删除工具"""

    name: str = "cos_delete"
    description: str = "从腾讯云COS对象存储删除文件"
    secret_id: str = Field(default_factory=lambda: os.getenv("COS_SECRET_ID", ""))
    secret_key: str = Field(default_factory=lambda: os.getenv("COS_SECRET_KEY", ""))
    region: str = Field(default_factory=lambda: os.getenv("COS_REGION", "ap-guangzhou"))
    bucket: str = Field(default_factory=lambda: os.getenv("COS_BUCKET", ""))

    _client: Optional[CosS3Client] = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        if self.secret_id and self.secret_key:
            self._client = _make_cos_client(self.secret_id, self.secret_key, self.region)

    @property
    def client(self) -> CosS3Client:
        if self._client is None:
            self._client = _make_cos_client(self.secret_id, self.secret_key, self.region)
        return self._client

    def _run(self, cos_path: str, bucket: Optional[str] = None) -> bool:
        bucket_name = bucket or self.bucket
        self.client.delete_object(
            Bucket=bucket_name,
            Key=cos_path,
        )
        return True
