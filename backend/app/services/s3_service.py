import uuid
from datetime import datetime
from pathlib import PurePosixPath
from typing import BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


def _client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def build_s3_key(filename: str) -> str:
    suffix = PurePosixPath(filename).suffix.lower() or ".mp4"
    today = datetime.utcnow().strftime("%Y/%m/%d")
    return f"videos/{today}/{uuid.uuid4().hex}{suffix}"


def upload_fileobj(fileobj: BinaryIO, s3_key: str, content_type: str | None = None) -> None:
    extra: dict[str, str] = {}
    if content_type:
        extra["ContentType"] = content_type
    try:
        _client().upload_fileobj(
            Fileobj=fileobj,
            Bucket=settings.s3_bucket,
            Key=s3_key,
            ExtraArgs=extra or None,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 upload failed: {exc}") from exc


def delete_object(s3_key: str) -> None:
    try:
        _client().delete_object(Bucket=settings.s3_bucket, Key=s3_key)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 delete failed: {exc}") from exc
