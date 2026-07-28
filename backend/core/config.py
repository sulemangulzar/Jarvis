import os


class Settings:
    app_name = "Jarvis API"
    api_prefix = "/api/v1"

    # Always set JWT_SECRET to a long random value in production.
    jwt_secret = os.getenv(
            "JWT_SECRET", "development-only-secret-change-me-before-production"
        )
    jwt_algorithm = "HS256"
    access_token_minutes = 15
    refresh_token_days = 7

    refresh_cookie_name = "refresh_token"
    cookie_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")


settings = Settings()
