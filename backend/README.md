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

Generate the token encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Never commit `.env` or place the Microsoft client secret in frontend variables. The backend requests `User.Read`, `Mail.ReadWrite`, `Calendars.ReadWrite`, and `Tasks.ReadWrite`. MSAL handles its reserved refresh-token scope automatically.

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
| `GET` | `/emails` | Lists recent emails |
| `GET` | `/emails/{email_id}` | Reads one email |
| `POST` | `/emails/drafts` | Creates an email draft only; never sends |
| `GET` | `/events` | Lists calendar events |
| `POST` | `/events` | Creates a calendar event |
| `PATCH` | `/events/{event_id}` | Updates a calendar event |
| `DELETE` | `/events/{event_id}` | Deletes a calendar event |
| `GET` | `/todos` | Lists tasks from the default To-Do list |
| `POST` | `/todos` | Creates a task |
| `PATCH` | `/todos/{task_id}` | Updates a task |
| `DELETE` | `/todos/{task_id}` | Deletes a task |
| `POST` | `/chat` | Sends a message to the LangGraph assistant |
| `GET` | `/scalar` | Opens the API reference |

The login route must be opened as a browser navigation. Do not call it with `fetch()` or Scalar's Try it out because OAuth requires a browser redirect. After Microsoft returns, the backend calls Graph `/me` with the server-side access token, stores safe identity fields in the database, stores only the internal user ID in the session, and redirects to `FRONTEND_URL`.

All Graph routes and `/chat` require an authenticated Jarvis session. Email creation is intentionally draft-only: the backend creates `/me/messages` and never calls `/sendMail`. Calendar and To-Do changes execute immediately.

The `/chat` endpoint uses LangGraph and the configured OpenAI model. Conversations and messages are stored in Neon. The assistant has explicit tools for reading email, creating drafts, calendar CRUD, and To-Do CRUD.

## Database

Neon is the intended database. Set `DATABASE_URL` to the PostgreSQL connection string from Neon when deploying. SQLite remains the local fallback. The startup code creates the initial `users` and encrypted `microsoft_token_caches` tables automatically for now. A later milestone should add Alembic migrations before the schema changes.
