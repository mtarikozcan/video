from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    gcs_object: str
    status: str
    operation_name: str | None = None
    duration_sec: float | None = None
    total_vehicles: int = 0
    created_at: datetime


class DetectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    object_type: str
    confidence: float
    timestamp_start_ms: int
    timestamp_end_ms: int


class ObjectCount(BaseModel):
    object_type: str
    count: int


class TimelineBucket(BaseModel):
    second: int
    count: int


class SummaryOut(BaseModel):
    video_id: int
    status: str
    total_vehicles: int
    duration_sec: float | None = None
    object_distribution: list[ObjectCount] = Field(default_factory=list)
    busiest_second: int | None = None
    busiest_second_count: int = 0
    timeline: list[TimelineBucket] = Field(default_factory=list)


class StatusOut(BaseModel):
    video_id: int
    status: str
    operation_name: str | None = None
    operation_done: bool | None = None
