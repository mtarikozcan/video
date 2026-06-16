from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Video
from app.schemas import VideoOut
from app.services import s3_service

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
