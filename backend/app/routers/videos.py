from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Detection, Video
from app.schemas import (
    DetectionOut,
    LabelCount,
    StatusOut,
    SummaryOut,
    TimelineBucket,
    VideoOut,
)
from app.services import rekognition, s3_service

router = APIRouter(prefix="/api/videos", tags=["videos"])

ALLOWED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-matroska", "application/octet-stream"}


@router.post("/upload", response_model=VideoOut, status_code=status.HTTP_201_CREATED)
def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)) -> Video:
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}",
        )

    s3_key = s3_service.build_s3_key(file.filename or "video.mp4")

    try:
        s3_service.upload_fileobj(file.file, s3_key, content_type=file.content_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    video = Video(
        filename=file.filename or "video.mp4",
        s3_key=s3_key,
        status="uploaded",
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.get("", response_model=list[VideoOut])
def list_videos(db: Session = Depends(get_db)) -> list[Video]:
    return list(db.scalars(select(Video).order_by(desc(Video.created_at))).all())


def _get_video_or_404(db: Session, video_id: int) -> Video:
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.post("/{video_id}/analyze", response_model=VideoOut)
def analyze_video(video_id: int, db: Session = Depends(get_db)) -> Video:
    video = _get_video_or_404(db, video_id)
    if video.status == "processing":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analysis already running")

    try:
        job_id = rekognition.start_label_detection(video.s3_key)
    except RuntimeError as exc:
        video.status = "failed"
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    video.job_id = job_id
    video.status = "processing"
    db.commit()
    db.refresh(video)
    return video


@router.get("/{video_id}/status", response_model=StatusOut)
def video_status(video_id: int, db: Session = Depends(get_db)) -> StatusOut:
    video = _get_video_or_404(db, video_id)

    if not video.job_id or video.status in {"uploaded", "done", "failed"}:
        return StatusOut(video_id=video.id, status=video.status, job_id=video.job_id)

    try:
        result = rekognition.fetch_label_detection(video.job_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if result.status == "SUCCEEDED":
        db.query(Detection).filter(Detection.video_id == video.id).delete()
        total = 0
        for det in result.detections:
            db.add(
                Detection(
                    video_id=video.id,
                    label=det.label,
                    timestamp_ms=det.timestamp_ms,
                    confidence=det.confidence,
                    count=det.count,
                )
            )
            total += det.count
        video.total_vehicles = total
        if result.duration_ms is not None:
            video.duration_sec = round(result.duration_ms / 1000.0, 3)
        video.status = "done"
        db.commit()
        db.refresh(video)
    elif result.status == "FAILED":
        video.status = "failed"
        db.commit()
        db.refresh(video)

    return StatusOut(
        video_id=video.id,
        status=video.status,
        job_id=video.job_id,
        rekognition_status=result.status,
    )


@router.get("/{video_id}/detections", response_model=list[DetectionOut])
def list_detections(
    video_id: int,
    label: str | None = None,
    db: Session = Depends(get_db),
) -> list[Detection]:
    _get_video_or_404(db, video_id)
    stmt = select(Detection).where(Detection.video_id == video_id)
    if label:
        stmt = stmt.where(Detection.label == label)
    stmt = stmt.order_by(asc(Detection.timestamp_ms))
    return list(db.scalars(stmt).all())


@router.get("/{video_id}/summary", response_model=SummaryOut)
def video_summary(video_id: int, db: Session = Depends(get_db)) -> SummaryOut:
    video = _get_video_or_404(db, video_id)
    detections = list(
        db.scalars(
            select(Detection)
            .where(Detection.video_id == video_id)
            .order_by(asc(Detection.timestamp_ms))
        ).all()
    )

    label_counter: Counter[str] = Counter()
    per_second: dict[int, int] = defaultdict(int)
    for det in detections:
        label_counter[det.label] += det.count
        per_second[det.timestamp_ms // 1000] += det.count

    timeline = [
        TimelineBucket(second=sec, count=cnt) for sec, cnt in sorted(per_second.items())
    ]
    busiest = max(per_second.items(), key=lambda kv: kv[1], default=(None, 0))

    return SummaryOut(
        video_id=video.id,
        status=video.status,
        total_vehicles=video.total_vehicles,
        duration_sec=video.duration_sec,
        label_distribution=[
            LabelCount(label=lbl, count=cnt)
            for lbl, cnt in sorted(label_counter.items(), key=lambda kv: -kv[1])
        ],
        busiest_second=busiest[0],
        busiest_second_count=busiest[1],
        timeline=timeline,
    )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: int, db: Session = Depends(get_db)) -> Response:
    video = _get_video_or_404(db, video_id)
    try:
        s3_service.delete_object(video.s3_key)
    except RuntimeError:
        pass  # S3 delete failure should not block DB cleanup
    db.delete(video)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
