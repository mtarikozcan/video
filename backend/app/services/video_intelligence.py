from dataclasses import dataclass

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import videointelligence_v1 as vi
from google.protobuf.duration_pb2 import Duration

from app.config import settings

# Object-tracking entity descriptions (lowercase) we treat as vehicles.
# Video Intelligence emits entity descriptions like "car", "truck", etc.
VEHICLE_ENTITIES = {
    "car",
    "truck",
    "bus",
    "motorcycle",
    "motorbike",
    "van",
    "vehicle",
}

# Display names normalized to four classes for reporting parity.
VEHICLE_DISPLAY: dict[str, str] = {
    "car": "Car",
    "truck": "Truck",
    "bus": "Bus",
    "motorcycle": "Motorcycle",
    "motorbike": "Motorcycle",
    "van": "Truck",  # group vans with trucks for the four-class taxonomy
    "vehicle": "Vehicle",  # generic fallback
}


@dataclass
class TrackedObject:
    object_type: str
    confidence: float
    timestamp_start_ms: int
    timestamp_end_ms: int


@dataclass
class VideoIntelligenceResult:
    done: bool
    objects: list[TrackedObject]
    duration_ms: int | None
    error: str | None = None


_service_client: vi.VideoIntelligenceServiceClient | None = None


def _client() -> vi.VideoIntelligenceServiceClient:
    global _service_client
    if _service_client is None:
        _service_client = vi.VideoIntelligenceServiceClient()
    return _service_client


def start_object_tracking(gcs_uri: str) -> str:
    """Start an OBJECT_TRACKING annotation. Returns the long-running operation name."""
    try:
        operation = _client().annotate_video(
            request={
                "features": [vi.Feature.OBJECT_TRACKING],
                "input_uri": gcs_uri,
            }
        )
    except GoogleAPICallError as exc:
        raise RuntimeError(f"Video Intelligence start failed: {exc}") from exc
    return operation.operation.name


def _duration_to_ms(d: Duration | None) -> int:
    if d is None:
        return 0
    return int(d.seconds * 1000 + d.nanos // 1_000_000)


def fetch_object_tracking(operation_name: str) -> VideoIntelligenceResult:
    """Poll a long-running operation. Parse OBJECT_TRACKING annotations on completion."""
    client = _client()
    try:
        op_proto = client.transport.operations_client.get_operation(operation_name)
    except GoogleAPICallError as exc:
        raise RuntimeError(f"Video Intelligence fetch failed: {exc}") from exc

    if not op_proto.done:
        return VideoIntelligenceResult(done=False, objects=[], duration_ms=None)

    if op_proto.HasField("error") and op_proto.error.code != 0:
        return VideoIntelligenceResult(
            done=True, objects=[], duration_ms=None, error=op_proto.error.message
        )

    response = vi.AnnotateVideoResponse.deserialize(op_proto.response.value)

    objects: list[TrackedObject] = []
    duration_ms: int | None = None
    threshold = settings.video_intelligence_min_confidence

    for result in response.annotation_results:
        if result.segment and result.segment.end_time_offset is not None:
            duration_ms = max(duration_ms or 0, _duration_to_ms(result.segment.end_time_offset))

        for obj in result.object_annotations:
            entity = (obj.entity.description or "").strip().lower()
            if entity not in VEHICLE_ENTITIES:
                continue
            if obj.confidence < threshold:
                continue
            objects.append(
                TrackedObject(
                    object_type=VEHICLE_DISPLAY.get(entity, entity.title()),
                    confidence=float(obj.confidence),
                    timestamp_start_ms=_duration_to_ms(obj.segment.start_time_offset),
                    timestamp_end_ms=_duration_to_ms(obj.segment.end_time_offset),
                )
            )

    return VideoIntelligenceResult(done=True, objects=objects, duration_ms=duration_ms)
