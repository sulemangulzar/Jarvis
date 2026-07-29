# Jarvis backend

The backend is a FastAPI application. It currently provides health checks, session configuration, Microsoft OAuth routes, and a local/Neon-ready database layer.

## Run locally

From the `backend` directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

The canonical entrypoint is `app.main:app`. The root `main.py` is a small compatibility file, so both commands work:

```bash
uvicorn main:app --reload
uvicorn app.main:app --reload
```

## Configuration

Copy `.env.example` to `.env` and replace the placeholder values. Generate a session secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Never commit `.env` or place the Microsoft client secret in frontend variables.

## Current endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health/live` | Confirms the process is running |
| `GET` | `/health/ready` | Checks that the database connection is available |
| `GET` | `/auth/microsoft/login` | Starts Microsoft login in a browser |
| `GET` / `POST` | `/auth/microsoft/callback` | Completes the OAuth flow |
| `GET` | `/auth/status` | Returns the current authentication status |
| `POST` | `/auth/logout` | Clears the session |
| `GET` | `/auth/microsoft/me` | Returns the signed-in user (legacy convenience route) |
| `GET` | `/scalar` | Opens the API reference |

The login route must be opened as a browser navigation. Do not call it with `fetch()` or Scalar's Try it out because OAuth requires a browser redirect. After Microsoft returns, the backend calls Graph `/me` with the server-side access token, stores safe identity fields in the database, stores only the internal user ID in the session, and redirects to `FRONTEND_URL`.

## Database

SQLite is used locally by default. Set `DATABASE_URL` to the PostgreSQL connection string from Neon when deploying. The current startup code creates the initial `users` table automatically. A later milestone should add Alembic migrations before the schema changes.
