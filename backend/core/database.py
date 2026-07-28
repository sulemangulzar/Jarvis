import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# SQLite is used locally. Set DATABASE_URL to the Neon PostgreSQL URL later.
SQLITE_PATH = Path(__file__).resolve().parent.parent / "jarvis.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Give one database session to each request and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
