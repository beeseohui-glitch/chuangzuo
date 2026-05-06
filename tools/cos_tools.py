"""
COS 工具 - 腾讯云对象存储读写
"""

import os
from typing import Optional
from qcloud_cos import CosConfig, CosS3Client
from crewai.tools import BaseTool
from pydantic import Field


class COSUploadTool(BaseTool):
    """COS 上传工具"""

    name: str = "cos_upload"
    description: str = "上传文件到腾讯云COS对象存储"

    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "ap-guangzhou",
        bucket: str = "",
    ):
        super().__init__()
        self.secret_id = secret_id or os.getenv("COS_SECRET_ID", "")
        self.secret_key = secret_key or os.getenv("COS_SECRET_KEY", "")
        self.region = region
        self.bucket = bucket
        self._client: Optional[CosS3Client] = None

    @property
    def client(self) -> CosS3Client:
        """获取 COS 客户端"""
        if self._client is None:
            config = CosConfig(
                Region=self.region,
                SecretId=self.secret_id,
                SecretKey=self.secret_key,
            )
            self._client = CosS3Client(config)
        return self._client

    def _run(
        self,
        file_path: str,
        cos_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        """
        BaseTool 接口 - 上传文件

        Args:
            file_path: 本地文件路径
            cos_path: COS 目标路径
            bucket: 可选的bucket名称

        Returns:
            str: COS 文件URL
        """
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
        """上传字节数据"""
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
        """上传文本"""
        return self.upload_bytes(text.encode("utf-8"), cos_path, bucket)


class COSDownloadTool(BaseTool):
    """COS 下载工具"""

    name: str = "cos_download"
    description: str = "从腾讯云COS对象存储下载文件"

    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "ap-guangzhou",
        bucket: str = "",
    ):
        super().__init__()
        self.secret_id = secret_id or os.getenv("COS_SECRET_ID", "")
        self.secret_key = secret_key or os.getenv("COS_SECRET_KEY", "")
        self.region = region
        self.bucket = bucket
        self._client: Optional[CosS3Client] = None

    @property
    def client(self) -> CosS3Client:
        """获取 COS 客户端"""
        if self._client is None:
            config = CosConfig(
                Region=self.region,
                SecretId=self.secret_id,
                SecretKey=self.secret_key,
            )
            self._client = CosS3Client(config)
        return self._client

    def _run(
        self,
        cos_path: str,
        local_path: str,
        bucket: Optional[str] = None,
    ) -> str:
        """
        BaseTool 接口 - 下载文件

        Args:
            cos_path: COS 文件路径
            local_path: 本地保存路径
            bucket: 可选的bucket名称

        Returns:
            str: 本地文件路径
        """
        bucket_name = bucket or self.bucket

        self.client.get_object(
            Bucket=bucket_name,
            Key=cos_path,
            DestPath=local_path,
        )

        return local_path

    def download_bytes(self, cos_path: str, bucket: Optional[str] = None) -> bytes:
        """下载为字节数据"""
        bucket_name = bucket or self.bucket

        response = self.client.get_object(
            Bucket=bucket_name,
            Key=cos_path,
        )

        return response["Body"].get_raw_stream().read()

    def download_text(self, cos_path: str, bucket: Optional[str] = None) -> str:
        """下载为文本"""
        return self.download_bytes(cos_path, bucket).decode("utf-8")


class COSDeleteTool(BaseTool):
    """COS 删除工具"""

    name: str = "cos_delete"
    description: str = "从腾讯云COS对象存储删除文件"

    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "ap-guangzhou",
        bucket: str = "",
    ):
        super().__init__()
        self.secret_id = secret_id or os.getenv("COS_SECRET_ID", "")
        self.secret_key = secret_key or os.getenv("COS_SECRET_KEY", "")
        self.region = region
        self.bucket = bucket
        self._client: Optional[CosS3Client] = None

    @property
    def client(self) -> CosS3Client:
        """获取 COS 客户端"""
        if self._client is None:
            config = CosConfig(
                Region=self.region,
                SecretId=self.secret_id,
                SecretKey=self.secret_key,
            )
            self._client = CosS3Client(config)
        return self._client

    def _run(self, cos_path: str, bucket: Optional[str] = None) -> bool:
        """删除文件"""
        bucket_name = bucket or self.bucket

        self.client.delete_object(
            Bucket=bucket_name,
            Key=cos_path,
        )

        return True
