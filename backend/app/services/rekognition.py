from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

VEHICLE_LABELS = {"Car", "Truck", "Bus", "Motorcycle"}
PARENT_VEHICLE_LABELS = {"Vehicle", "Transportation"}


@dataclass
class ParsedDetection:
    label: str
    timestamp_ms: int
    confidence: float
    count: int


@dataclass
class RekognitionResult:
    status: str  # IN_PROGRESS | SUCCEEDED | FAILED
    duration_ms: int | None
    detections: list[ParsedDetection]
    status_message: str | None = None


def _client():
    return boto3.client(
        "rekognition",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def start_label_detection(s3_key: str) -> str:
    """Start an async Rekognition label-detection job. Returns the JobId."""
    try:
        response = _client().start_label_detection(
            Video={"S3Object": {"Bucket": settings.s3_bucket, "Name": s3_key}},
            MinConfidence=settings.rekognition_min_confidence,
            Features=["GENERAL_LABELS"],
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Rekognition start failed: {exc}") from exc
    return response["JobId"]


def _is_vehicle_label(label: dict) -> bool:
    name = label.get("Name", "")
    if name in VEHICLE_LABELS:
        return True
    parents = {p.get("Name") for p in label.get("Parents", [])}
    return bool(parents & PARENT_VEHICLE_LABELS) and name not in {"Vehicle", "Transportation"}


def _instance_count(label: dict) -> int:
    instances = label.get("Instances") or []
    return max(1, len(instances))


def fetch_label_detection(job_id: str) -> RekognitionResult:
    """Poll a Rekognition job. If SUCCEEDED, parse all vehicle detections."""
    client = _client()
    try:
        first = client.get_label_detection(JobId=job_id, MaxResults=1000, SortBy="TIMESTAMP")
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Rekognition fetch failed: {exc}") from exc

    status = first.get("JobStatus", "IN_PROGRESS")
    if status != "SUCCEEDED":
        return RekognitionResult(
            status=status,
            duration_ms=None,
            detections=[],
            status_message=first.get("StatusMessage"),
        )

    duration_ms = first.get("VideoMetadata", {}).get("DurationMillis")
    pages = [first]
    next_token = first.get("NextToken")
    while next_token:
        try:
            page = client.get_label_detection(
                JobId=job_id,
                MaxResults=1000,
                SortBy="TIMESTAMP",
                NextToken=next_token,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Rekognition fetch failed: {exc}") from exc
        pages.append(page)
        next_token = page.get("NextToken")

    detections: list[ParsedDetection] = []
    for page in pages:
        for entry in page.get("Labels", []):
            label = entry.get("Label") or {}
            if not _is_vehicle_label(label):
                continue
            detections.append(
                ParsedDetection(
                    label=label.get("Name", "Unknown"),
                    timestamp_ms=int(entry.get("Timestamp", 0)),
                    confidence=float(label.get("Confidence", 0.0)),
                    count=_instance_count(label),
                )
            )
    return RekognitionResult(
        status="SUCCEEDED",
        duration_ms=duration_ms,
        detections=detections,
    )
