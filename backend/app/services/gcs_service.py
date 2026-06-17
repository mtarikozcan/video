import uuid
from datetime import datetime
from pathlib import PurePosixPath
from typing import BinaryIO

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from app.config import settings

_client: storage.Client | None = None


def _storage_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client(project=settings.gcp_project)
    return _client


def build_object_name(filename: str) -> str:
    suffix = PurePosixPath(filename).suffix.lower() or ".mp4"
    today = datetime.utcnow().strftime("%Y/%m/%d")
    return f"videos/{today}/{uuid.uuid4().hex}{suffix}"


def gs_uri(object_name: str) -> str:
    return f"gs://{settings.gcs_bucket}/{object_name}"


def upload_fileobj(fileobj: BinaryIO, object_name: str, content_type: str | None = None) -> None:
    try:
        bucket = _storage_client().bucket(settings.gcs_bucket)
        blob = bucket.blob(object_name)
        blob.upload_from_file(fileobj, content_type=content_type, rewind=True)
    except GoogleCloudError as exc:
        raise RuntimeError(f"GCS upload failed: {exc}") from exc


def delete_object(object_name: str) -> None:
    try:
        bucket = _storage_client().bucket(settings.gcs_bucket)
        bucket.blob(object_name).delete()
    except GoogleCloudError as exc:
        raise RuntimeError(f"GCS delete failed: {exc}") from exc
