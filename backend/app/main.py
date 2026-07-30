from contextlib import asynccontextmanager


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.auth import router as microsoft_auth_router
from app.api.v1.auth import session_router
from app.api.v1.graph import router as graph_router
from app.api.v1.chat import router as chat_router
from app.core.config import get_settings
from app.db import Base, engine
import app.models.conversation  # noqa: F401
import app.models.oauth_flow  # noqa: F401
import app.models.token_cache  # noqa: F401
import app.models.user  # noqa: F401


def create_app() -> FastAPI:
    """Create the application and validate configuration before serving traffic."""
    try:
        settings = get_settings()
    except ValidationError as error:
        invalid_fields = sorted(
            {".".join(str(part) for part in item["loc"])
             for item in error.errors()}
        )
        fields = ", ".join(invalid_fields)
        raise RuntimeError(
            f"Invalid backend configuration. Fix these settings in .env: {fields}"
        ) from error

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # This is sufficient for the first local milestone. Add migrations before
        # making schema changes in production.
        Base.metadata.create_all(bind=engine)
        yield

    app = FastAPI(
        title="Jarvis API",
        description="Backend API for Jarvis.",
        version="0.1.0",
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_max_age,
        same_site=settings.session_same_site,
        https_only=settings.session_https_only,
    )

    app.include_router(microsoft_auth_router)
    app.include_router(session_router)
    app.include_router(graph_router)
    app.include_router(chat_router)

    @app.get("/health/live", tags=["System"])
    def liveness_check():
        return {"status": "ok"}

    @app.get("/health/ready", tags=["System"])
    def readiness_check():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready"},
            )
        return {"status": "ready"}

    @app.get("/health", include_in_schema=False)
    def health_check():
        return {"status": "ok"}

    @app.get("/scalar", include_in_schema=False, response_class=HTMLResponse)
    def scalar_api_reference():
        return """
        <!doctype html>
        <html>
          <head>
            <title>Jarvis API Reference</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
          </head>
          <body>
            <script id="api-reference" data-url="/openapi.json"></script>
            <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
          </body>
        </html>
        """

    return app


app = create_app()
