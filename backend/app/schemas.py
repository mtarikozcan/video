from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    s3_key: str
    status: str
    job_id: str | None = None
    duration_sec: float | None = None
    total_vehicles: int = 0
    created_at: datetime


class DetectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    label: str
    timestamp_ms: int
    confidence: float
    count: int


class LabelCount(BaseModel):
    label: str
    count: int


class TimelineBucket(BaseModel):
    second: int
    count: int


class SummaryOut(BaseModel):
    video_id: int
    status: str
    total_vehicles: int
    duration_sec: float | None = None
    label_distribution: list[LabelCount] = Field(default_factory=list)
    busiest_second: int | None = None
    busiest_second_count: int = 0
    timeline: list[TimelineBucket] = Field(default_factory=list)


class StatusOut(BaseModel):
    video_id: int
    status: str
    job_id: str | None = None
    rekognition_status: str | None = None
