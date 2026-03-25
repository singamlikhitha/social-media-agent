import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


def _build_engine():
    db_url = settings.DATABASE_URL

    connect_args = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False

    return create_engine(
        db_url,
        connect_args=connect_args,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,
    )


engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
