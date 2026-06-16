import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import videos as videos_router

logger = logging.getLogger("ucuncugoz")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001
        logger.warning("init_db skipped: %s", exc)
    yield


app = FastAPI(title="UcuncuGoz API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(videos_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
