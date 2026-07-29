# Keep this file so the existing command still works:
# uvicorn main:app --reload
from app.main import app

__all__ = ["app"]
