from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create any missing tables defined on Base.metadata.

    Models must be imported (and therefore registered on Base.metadata) before
    this runs. Both main.py and routers/videos.py import app.models at module
    load, but we re-import here as a defensive no-op.
    """
    import logging

    from app import models  # noqa: F401  -- ensure models are registered

    logger = logging.getLogger("ucuncugoz")
    tables = sorted(Base.metadata.tables.keys())
    logger.info("init_db: ensuring tables %s on dialect %s", tables, engine.dialect.name)
    Base.metadata.create_all(bind=engine)
    logger.info("init_db: schema ensured")
