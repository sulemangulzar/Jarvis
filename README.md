# Jarvis

Jarvis is a text-based personal assistant that connects to Microsoft through OAuth and uses LangGraph to work with Microsoft Graph.

Jarvis can currently:

- Sign users in with Microsoft Entra ID.
- Store users in Neon/PostgreSQL.
- Store encrypted MSAL token caches in Neon.
- Read email.
- Create email drafts.
- Never send email.
- Create, read, update, and delete calendar events.
- Create, read, update, and delete Microsoft To-Do tasks.
- Chat with the user through a LangGraph agent.
- Persist conversations and messages.
- Run as Docker containers.

## Architecture

```text
React + Vite + Tailwind
        |
        | session-cookie requests
        v
FastAPI backend
        |
        +-- Microsoft OAuth with MSAL
        +-- Microsoft Graph email/calendar/To-Do tools
        +-- LangGraph assistant
        +-- OpenAI model
        +-- SQLAlchemy
        v
Neon PostgreSQL
```

The browser never receives Microsoft access tokens, refresh tokens, client secrets, or OpenAI keys. The backend stores only safe identity data in the session cookie and keeps the encrypted MSAL token cache server-side.

## Project structure

```text
Jarvis/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── db.py
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── graph.py
│   │   ├── core/config.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── token_cache.py
│   │   │   └── conversation.py
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   ├── .env.example
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/api.js
│   │   └── App.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── .dockerignore
```

## Requirements

- Python 3.13 or later
- Node.js 22 or later
- Docker Desktop or OrbStack for container testing
- A Microsoft Entra application registration
- A Neon PostgreSQL database
- An OpenAI API key for the LangGraph assistant

## Microsoft Entra setup

Create an application registration in Microsoft Entra ID.

For personal Microsoft accounts, choose:

```text
Accounts in any organizational directory and personal Microsoft accounts
```

For local development, register this exact redirect URI:

```text
http://localhost:8000/auth/microsoft/callback
```

For production, register the deployed callback URI exactly, for example:

```text
https://your-api-domain.com/auth/microsoft/callback
```

Create a client secret under:

```text
Certificates & secrets → New client secret
```

Use the secret **Value**, not the secret ID.

### Delegated permissions

Add only the permissions currently needed:

```text
User.Read
Mail.ReadWrite
Calendars.ReadWrite
Tasks.ReadWrite
```

`offline_access` is handled automatically by MSAL and must not be manually added to the Python scope list because it is a reserved scope.

## Backend configuration

Copy the example file:

```bash
cd backend
cp .env.example .env
```

Fill in `backend/.env`:

```env
APP_ENV=development
FRONTEND_URL=http://localhost:5173

# Neon PostgreSQL connection string
DATABASE_URL=postgresql://username:password@your-neon-host/neondb?sslmode=require

MICROSOFT_CLIENT_ID=your-application-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret-value
MICROSOFT_TENANT=common
MICROSOFT_REDIRECT_URI=http://localhost:8000/auth/microsoft/callback

SESSION_SECRET=your-long-random-session-secret
SESSION_COOKIE_NAME=jarvis_session
SESSION_MAX_AGE=604800
SESSION_HTTPS_ONLY=false

TOKEN_ENCRYPTION_KEY=your-fernet-key

OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

Generate secrets:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Do not commit `backend/.env`.

## Frontend configuration

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Never put Microsoft client secrets, Microsoft tokens, database credentials, or OpenAI keys in frontend variables.

## Run locally

### Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend is also available through:

```bash
uv run uvicorn app.main:app --reload
```

### Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Use `localhost` consistently for both the frontend and OAuth redirect. Do not mix `localhost` and `127.0.0.1` in browser URLs.

## API routes

### Health

```text
GET /health/live
GET /health/ready
```

### Authentication

```text
GET  /auth/microsoft/login
GET  /auth/microsoft/callback
POST /auth/microsoft/callback
GET  /auth/status
POST /auth/logout
```

Start Microsoft login with browser navigation. Do not call the login endpoint with `fetch()`.

### Chat

```text
POST /chat
```

Example:

```json
{
  "message": "Show my latest emails"
}
```

### Email

```text
GET  /emails
GET  /emails/{email_id}
POST /emails/drafts
```

Email is draft-only. Jarvis creates `/me/messages` and never calls `/sendMail`.

### Calendar

```text
GET    /events
POST   /events
PATCH  /events/{event_id}
DELETE /events/{event_id}
```

### Microsoft To-Do

```text
GET    /todos
POST   /todos
PATCH  /todos/{task_id}
DELETE /todos/{task_id}
```

### API reference

```text
http://localhost:8000/scalar
```

## Database

Neon is the intended production database. The initial tables are:

```text
users
microsoft_token_caches
conversations
conversation_messages
```

The application currently creates these tables on startup with SQLAlchemy. Before making future schema changes in production, add Alembic migrations.

The MSAL cache is encrypted with `TOKEN_ENCRYPTION_KEY` before it is saved to Neon.

## Testing

Run backend tests:

```bash
PYTHONPATH=backend uv run --project backend pytest backend/tests -q
```

Run the frontend production build:

```bash
npm run build --prefix frontend
```

The tests mock Microsoft Graph, MSAL, OpenAI/LangGraph, and database behavior where appropriate. They do not call real Microsoft or OpenAI services.

## Docker

Make sure `backend/.env` is configured first.

From the repository root:

```bash
docker compose build
docker compose up
```

Open:

```text
http://localhost:5173
```

Stop containers:

```bash
docker compose down
```

The backend container listens on port `8000`. The frontend Nginx container listens on port `80`, mapped to local port `5173` by Compose.

If Docker reports that the Docker API is unavailable, start OrbStack or Docker Desktop first:

```bash
open -a OrbStack
```

## Deployment checklist

Recommended first deployment:

- Deploy the backend as a web service.
- Deploy the frontend as a separate static/container service.
- Use Neon for PostgreSQL.
- Set all secrets in the hosting provider’s environment settings.
- Enable HTTPS.
- Set `SESSION_HTTPS_ONLY=true`.
- Set `FRONTEND_URL` to the exact public frontend URL.
- Set `MICROSOFT_REDIRECT_URI` to the exact public backend callback URL.
- Register that callback URL in Microsoft Entra.
- Confirm `/health/live` and `/health/ready` after deployment.

Example production values:

```env
APP_ENV=production
FRONTEND_URL=https://app.example.com
MICROSOFT_REDIRECT_URI=https://api.example.com/auth/microsoft/callback
SESSION_HTTPS_ONLY=true
SESSION_MAX_AGE=604800
```

## Security decisions

- OAuth state is validated through MSAL.
- Session cookies are signed by Starlette.
- Production cookies must use HTTPS.
- Access and refresh tokens are not stored in browser storage.
- Microsoft tokens are encrypted before database storage.
- Client secrets are backend-only.
- OpenAI keys are backend-only.
- CORS uses an exact configured frontend origin.
- Email sending is intentionally not implemented.
- Graph errors are sanitized before returning to users.
- Authorization headers and tokens are not logged.

## Current limitations

- The initial schema uses `create_all()` instead of Alembic migrations.
- The MSAL token cache is persisted server-side, but cache encryption key rotation is not implemented yet.
- The frontend currently uses one chat workspace rather than multiple conversation tabs.
- Live Microsoft, Neon, OpenAI, and hosting behavior requires real production credentials and network access.
- The current To-Do implementation uses the user’s first available To-Do list.

## Suggested next improvements

- Add Alembic migrations.
- Add conversation history loading to the frontend.
- Add dedicated calendar, mail, and To-Do dashboard views.
- Add server-side rate limiting.
- Add structured audit events without logging sensitive values.
- Add production monitoring and error tracking.
