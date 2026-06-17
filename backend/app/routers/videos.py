from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Detection, Video
from app.schemas import (
    DetectionOut,
    ObjectCount,
    StatusOut,
    SummaryOut,
    TimelineBucket,
    VideoOut,
)
from app.services import gcs_service, video_intelligence

router = APIRouter(prefix="/api/videos", tags=["videos"])

ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "application/octet-stream",
}


def _get_video_or_404(db: Session, video_id: int) -> Video:
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.post("/upload", response_model=VideoOut, status_code=status.HTTP_201_CREATED)
def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)) -> Video:
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}",
        )

    object_name = gcs_service.build_object_name(file.filename or "video.mp4")
    try:
        gcs_service.upload_fileobj(file.file, object_name, content_type=file.content_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    video = Video(
        filename=file.filename or "video.mp4",
        gcs_object=object_name,
        status="uploaded",
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.get("", response_model=list[VideoOut])
def list_videos(db: Session = Depends(get_db)) -> list[Video]:
    return list(db.scalars(select(Video).order_by(desc(Video.created_at))).all())


@router.post("/{video_id}/analyze", response_model=VideoOut)
def analyze_video(video_id: int, db: Session = Depends(get_db)) -> Video:
    video = _get_video_or_404(db, video_id)
    if video.status == "processing":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analysis already running")

    try:
        operation_name = video_intelligence.start_object_tracking(
            gcs_service.gs_uri(video.gcs_object)
        )
    except RuntimeError as exc:
        video.status = "failed"
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    video.operation_name = operation_name
    video.status = "processing"
    db.commit()
    db.refresh(video)
    return video


@router.get("/{video_id}/status", response_model=StatusOut)
def video_status(video_id: int, db: Session = Depends(get_db)) -> StatusOut:
    video = _get_video_or_404(db, video_id)

    if not video.operation_name or video.status in {"uploaded", "done", "failed"}:
        return StatusOut(
            video_id=video.id,
            status=video.status,
            operation_name=video.operation_name,
        )

    try:
        result = video_intelligence.fetch_object_tracking(video.operation_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if result.done and result.error:
        video.status = "failed"
        db.commit()
        db.refresh(video)
    elif result.done:
        db.query(Detection).filter(Detection.video_id == video.id).delete()
        for obj in result.objects:
            db.add(
                Detection(
                    video_id=video.id,
                    object_type=obj.object_type,
                    confidence=obj.confidence,
                    timestamp_start_ms=obj.timestamp_start_ms,
                    timestamp_end_ms=obj.timestamp_end_ms,
                )
            )
        video.total_vehicles = len(result.objects)
        if result.duration_ms is not None:
            video.duration_sec = round(result.duration_ms / 1000.0, 3)
        video.status = "done"
        db.commit()
        db.refresh(video)

    return StatusOut(
        video_id=video.id,
        status=video.status,
        operation_name=video.operation_name,
        operation_done=result.done,
    )


@router.get("/{video_id}/detections", response_model=list[DetectionOut])
def list_detections(
    video_id: int,
    object_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[Detection]:
    _get_video_or_404(db, video_id)
    stmt = select(Detection).where(Detection.video_id == video_id)
    if object_type:
        stmt = stmt.where(Detection.object_type == object_type)
    stmt = stmt.order_by(asc(Detection.timestamp_start_ms))
    return list(db.scalars(stmt).all())


@router.get("/{video_id}/summary", response_model=SummaryOut)
def video_summary(video_id: int, db: Session = Depends(get_db)) -> SummaryOut:
    video = _get_video_or_404(db, video_id)
    detections = list(
        db.scalars(
            select(Detection)
            .where(Detection.video_id == video_id)
            .order_by(asc(Detection.timestamp_start_ms))
        ).all()
    )

    object_counter: Counter[str] = Counter()
    per_second: dict[int, int] = defaultdict(int)
    for det in detections:
        object_counter[det.object_type] += 1
        start_sec = det.timestamp_start_ms // 1000
        end_sec = max(start_sec, det.timestamp_end_ms // 1000)
        for sec in range(start_sec, end_sec + 1):
            per_second[sec] += 1

    timeline = [
        TimelineBucket(second=sec, count=cnt) for sec, cnt in sorted(per_second.items())
    ]
    busiest = max(per_second.items(), key=lambda kv: kv[1], default=(None, 0))

    return SummaryOut(
        video_id=video.id,
        status=video.status,
        total_vehicles=video.total_vehicles,
        duration_sec=video.duration_sec,
        object_distribution=[
            ObjectCount(object_type=lbl, count=cnt)
            for lbl, cnt in sorted(object_counter.items(), key=lambda kv: -kv[1])
        ],
        busiest_second=busiest[0],
        busiest_second_count=busiest[1],
        timeline=timeline,
    )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: int, db: Session = Depends(get_db)) -> Response:
    video = _get_video_or_404(db, video_id)
    try:
        gcs_service.delete_object(video.gcs_object)
    except RuntimeError:
        pass
    db.delete(video)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
