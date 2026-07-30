import os

# Shared test settings are defined before application modules are imported.
os.environ["APP_ENV"] = "development"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["MICROSOFT_CLIENT_ID"] = "test-client-id"
os.environ["MICROSOFT_CLIENT_SECRET"] = "test-client-secret"
os.environ["MICROSOFT_REDIRECT_URI"] = (
    "http://localhost:8000/auth/microsoft/callback"
)
os.environ["SESSION_SECRET"] = "test-session-secret-that-is-long-enough-123"
os.environ["TOKEN_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
