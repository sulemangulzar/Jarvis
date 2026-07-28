from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing the models registers their tables with SQLAlchemy metadata.
import models.auth  # noqa: F401
from apis.v1.auth import router as auth_router
from core.config import settings
from core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This is intentionally simple for SQLite. Use Alembic migrations when
    # moving to Neon/PostgreSQL.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok"}
