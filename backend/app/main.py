import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env into os.environ before anything else so that libraries which read
# directly from the process environment (e.g. google.auth picking up
# GOOGLE_APPLICATION_CREDENTIALS) see the configured values.
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import init_db  # noqa: E402
from app.routers import videos as videos_router  # noqa: E402

logger = logging.getLogger("ucuncugoz")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Belt-and-suspenders: if the credential path came in via .env / pydantic
    # but not yet via os.environ (e.g. when something imported before
    # load_dotenv ran), publish it now so google.auth.default() finds it.
    if settings.google_application_credentials:
        os.environ.setdefault(
            "GOOGLE_APPLICATION_CREDENTIALS", settings.google_application_credentials
        )
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001
        logger.warning("init_db skipped: %s", exc)
    yield


app = FastAPI(title="UcuncuGoz API", version="0.2.0", lifespan=lifespan)

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
