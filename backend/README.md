# Jarvis backend

Beginner-friendly FastAPI authentication with JWT access tokens, refresh-token cookies, and SQLite.

## Run locally

```bash
uv sync
uv run uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to try every endpoint.

For production, set environment variables before starting the server:

```bash
JWT_SECRET="a-long-random-secret" COOKIE_SECURE=true FRONTEND_URL="https://your-app.com" uv run uvicorn main:app
```

`COOKIE_SECURE` should remain `false` for local HTTP development and must be `true` under production HTTPS.

## Authentication endpoints

All endpoints start with `/api/v1/auth`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/register` | Create a user, return an access token, and set a refresh cookie |
| POST | `/login` | Log in, return an access token, and set a refresh cookie |
| POST | `/refresh` | Rotate the refresh token and return a new access token |
| POST | `/logout` | Delete all of the user's refresh-token records and clear the cookie |
| GET | `/me` | Return the current user using a Bearer access token |

Register and login accept JSON:

```json
{
  "email": "person@example.com",
  "password": "password123"
}
```

Send the returned access token to protected endpoints:

```text
Authorization: Bearer <access_token>
```

In a browser, include credentials on requests that use the refresh cookie:

```javascript
await fetch("http://127.0.0.1:8000/api/v1/auth/refresh", {
  method: "POST",
  credentials: "include",
});
```

The access token is deliberately not written to browser storage by the backend. Keep it in frontend memory. The refresh token is an `HttpOnly` cookie, so JavaScript cannot read it.

## Database

The app creates `jarvis.db` automatically. Access tokens are stateless and are not saved. Each refresh JWT contains a random ID (`jti`), and only that ID is saved in `refresh_tokens`. Logout deletes every saved refresh-token ID for the user, invalidating all sessions.

When moving to Neon, install a PostgreSQL driver, set the `DATABASE_URL` environment variable to your Neon connection string, and use Alembic migrations.
