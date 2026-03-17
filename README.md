# CreatorLab

CreatorLab is a full-stack SaaS-style workspace for creator tools: image upscaling, background removal, image compression, and PDF utilities in one polished dashboard.

Tagline: "All your creator tools in one smart workspace."

## Stack

- Frontend: Next.js 16, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLite, background workers
- Processing: Pillow, pypdf, reportlab, rembg (`u2net`), optional Real-ESRGAN
- Auth: email/password, session cookies, email verification, password reset
- Storage: local disk abstraction designed to support S3 later

## Features

- Landing page, pricing page, dashboard, admin page, history page, FAQ/about page
- Tool pages for:
  - AI Image Upscaler
  - Background Remover
  - Image Compressor
  - PDF Merge
  - PDF Split
  - Images to PDF
- Persistent job history in SQLite
- Queue-backed background processing with retry logic
- Per-user usage tracking and free-tier limits
- Local dev mail preview for verification and reset flows
- Dark/light mode
- Docker and reverse-proxy-ready deployment setup

## Project Structure

```text
CreatorLab/
|-- backend/
|   |-- app/
|   |   |-- api/routes/
|   |   |-- core/
|   |   |-- schemas/
|   |   `-- services/
|   |-- scripts/
|   |-- tests/
|   |-- .env.example
|   `-- .env.production.example
|-- frontend/
|   |-- app/
|   |-- components/
|   |-- lib/
|   |-- .env.example
|   `-- .env.production.example
|-- deploy/
|   `-- Caddyfile
|-- scripts/
|   |-- dev.ps1
|   `-- test.ps1
|-- docker-compose.yml
|-- docker-compose.prod.yml
`-- README.md
```

## Local Development on Windows

### Requirements

- Python 3.11+
- Node.js 20+
- npm

Optional for AI acceleration:

- NVIDIA GPU with CUDA-compatible drivers

### 1. Clone and prepare env files

```powershell
cd C:\Users\ll888\NewProject
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
```

### 2. Set up the backend

```powershell
cd C:\Users\ll888\NewProject\backend
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional AI runtime helper:

```powershell
python scripts\setup_ai_runtime.py
```

To install the suggested Torch and Real-ESRGAN packages automatically:

```powershell
python scripts\setup_ai_runtime.py --apply
```

### 3. Set up the frontend

```powershell
cd C:\Users\ll888\NewProject\frontend
npm install
```

### 4. Start both apps

Option A: use the helper script

```powershell
cd C:\Users\ll888\NewProject
.\scripts\dev.ps1
```

If PowerShell blocks local scripts on your machine, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

Option B: run each app manually

Backend:

```powershell
cd C:\Users\ll888\NewProject\backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd C:\Users\ll888\NewProject\frontend
npm run dev
```

### Local URLs

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Readiness: [http://localhost:8000/ready](http://localhost:8000/ready)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Auth Flows

### Signup and email verification

1. Create an account from `/signup`.
2. CreatorLab creates the user, signs them in, and sends a verification message.
3. In local development with `MAIL_BACKEND=local_file`, the verification email is stored on disk and previewable through the dev mail endpoints.
4. Open the verification link or submit the token on `/verify-email`.

If `REQUIRE_EMAIL_VERIFICATION=true`, the UI will prompt the user to verify. If `BLOCK_UNVERIFIED_USERS_FROM_JOBS=true`, unverified signed-in users cannot create new jobs.

For real delivery outside local development, switch `MAIL_BACKEND` to `smtp` and set the SMTP variables in the backend env file.

### Forgot password and reset password

1. Open `/forgot-password`.
2. Submit the account email.
3. CreatorLab generates a secure reset token with expiration.
4. Open the reset link from the email preview or use `/reset-password?token=...`.
5. Submit a new password.

Expired or invalid tokens return a clean error message instead of a generic failure.

### Local mail preview

Local development mail preview is available only when:

- `APP_ENV` is not `production`
- `MAIL_BACKEND=local_file`

Useful endpoints:

- `GET /api/auth/dev/messages/latest?email=...&kind=verification`
- `GET /api/auth/dev/messages/latest?email=...&kind=password_reset`
- `GET /api/auth/dev/messages/{message_id}`

Mail preview files are stored under `backend/storage/mail`.

## Running Tests

### Full local check

```powershell
cd C:\Users\ll888\NewProject
.\scripts\test.ps1
```

If local execution policy blocks it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

That script runs:

- frontend production build
- backend compile check
- backend smoke test
- live API tests

### Manual backend tests

```powershell
cd C:\Users\ll888\NewProject\backend
.\.venv\Scripts\activate
python -m compileall app scripts
python scripts\e2e_smoke.py
pytest -q tests\test_live_api.py
```

## Environment Variables

### Frontend

Copy [frontend/.env.example](C:\Users\ll888\NewProject\frontend\.env.example) to `frontend/.env.local` for local development.

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | Browser-facing backend URL. Use `http://localhost:8000` locally. |
| `API_URL_INTERNAL` | Server-side URL used by Next.js for SSR and server fetches. Use `http://backend:8000` in Docker. |

### Backend

Copy [backend/.env.example](C:\Users\ll888\NewProject\backend\.env.example) to `backend/.env` for local development. For public deployment, start from [backend/.env.production.example](C:\Users\ll888\NewProject\backend\.env.production.example).

Core settings:

| Variable | Purpose |
|---|---|
| `APP_ENV` | Environment name, such as `development` or `production`. |
| `CORS_ORIGINS` | JSON array or comma-separated list of allowed frontend origins. |
| `STORAGE_ROOT` | Base path for uploads, outputs, mail previews, and SQLite data. |
| `DATABASE_PATH` | SQLite file path. |
| `STORAGE_BACKEND` | Current storage driver. `local` is implemented; structure is ready for S3 later. |

Uploads and processing:

| Variable | Purpose |
|---|---|
| `MAX_UPLOAD_MB` | Per-file upload limit. |
| `MAX_BATCH_UPLOAD_MB` | Total request file limit for multi-file jobs. |
| `MAX_REQUEST_MB` | Hard request-body cap for tool endpoints. |
| `TEMP_FILE_TTL_HOURS` | Age limit for temp files before cleanup. |
| `OUTPUT_FILE_TTL_HOURS` | Age limit for output files before cleanup. |
| `WORKER_THREADS` | Number of job worker threads. |
| `WORKER_QUEUE_SIZE` | Max queued jobs before the API returns `503`. |
| `JOB_MAX_RETRIES` | Retry count for failed jobs. |
| `CLEANUP_INTERVAL_SECONDS` | Cleanup frequency. |
| `UPLOAD_RATE_LIMIT_PER_MINUTE` | Upload budget per minute. Heavy tools consume more weight. |

AI/runtime:

| Variable | Purpose |
|---|---|
| `REALESRGAN_MODEL_NAME` | Real-ESRGAN model name metadata. |
| `REALESRGAN_WEIGHTS_URL` | Weights URL used by the Real-ESRGAN path. |
| `REMBG_MODEL_NAME` | Background removal model name. |

Logging:

| Variable | Purpose |
|---|---|
| `LOG_LEVEL` | Logging level. |
| `LOG_JSON` | Emits structured JSON logs when `true`. |

Auth and session:

| Variable | Purpose |
|---|---|
| `AUTH_SECRET_KEY` | Secret used for auth token/session signing. Set a strong random value in production. |
| `SESSION_COOKIE_NAME` | Cookie name for app sessions. |
| `SESSION_TTL_DAYS` | Session lifetime. |
| `COOKIE_DOMAIN` | Cookie domain for public deployment. |
| `SESSION_COOKIE_SECURE` | Must be `true` behind HTTPS in production. |
| `SESSION_COOKIE_SAMESITE` | `lax`, `strict`, or `none`. |
| `REQUIRE_AUTH_FOR_JOBS` | If `true`, only signed-in users can create jobs. |
| `REQUIRE_EMAIL_VERIFICATION` | Enables email verification flow. |
| `BLOCK_UNVERIFIED_USERS_FROM_JOBS` | Prevents signed-in but unverified users from creating jobs. |

Public URLs and mail:

| Variable | Purpose |
|---|---|
| `APP_PUBLIC_URL` | Public frontend URL used in auth emails. |
| `API_PUBLIC_URL` | Public backend URL if needed for links and downloads. |
| `MAIL_BACKEND` | Mail provider. Use `local_file` for local preview or `smtp` for real delivery. |
| `MAIL_FROM_EMAIL` | Sender address. |
| `SMTP_HOST` | SMTP host when `MAIL_BACKEND=smtp`. |
| `SMTP_PORT` | SMTP port. |
| `SMTP_USERNAME` | SMTP username or API key. |
| `SMTP_PASSWORD` | SMTP password or provider secret. |
| `SMTP_USE_TLS` | Enables STARTTLS for SMTP. |
| `SMTP_USE_SSL` | Enables implicit SSL SMTP. |
| `SMTP_TIMEOUT_SECONDS` | SMTP connection timeout. |
| `EMAIL_VERIFICATION_TTL_HOURS` | Verification token lifetime. |
| `PASSWORD_RESET_TTL_MINUTES` | Reset token lifetime. |

## Docker

### Local Docker stack

```powershell
cd C:\Users\ll888\NewProject
docker compose up --build
```

This starts:

- backend on port `8000`
- frontend on port `3000`

### Production Docker stack

1. Create `backend/.env.production` from [backend/.env.production.example](C:\Users\ll888\NewProject\backend\.env.production.example).
2. Create `frontend/.env.production` from [frontend/.env.production.example](C:\Users\ll888\NewProject\frontend\.env.production.example) if you want to keep a checked local copy.
3. Set `SITE_ADDRESS` for Caddy, either in your shell or a `.env` file next to `docker-compose.prod.yml`.
4. Make sure `SESSION_COOKIE_SECURE=true`, `AUTH_SECRET_KEY` is strong, and `APP_PUBLIC_URL` / `API_PUBLIC_URL` point at the public domain.

Run:

```powershell
cd C:\Users\ll888\NewProject
docker compose -f docker-compose.prod.yml up --build -d
```

The production stack contains:

- `backend`
- `frontend`
- `proxy` (Caddy)

Reverse proxy behavior is defined in [deploy/Caddyfile](C:\Users\ll888\NewProject\deploy\Caddyfile):

- `/api/*`, `/downloads/*`, `/health`, `/ready`, `/docs`, `/openapi.json` go to the backend
- everything else goes to the frontend

This keeps frontend/backend communication production-safe without exposing the internal container network directly to the browser.

## Production Deployment Checklist

- Set a real `AUTH_SECRET_KEY`
- Set `SESSION_COOKIE_SECURE=true`
- Set `COOKIE_DOMAIN` to your public domain if needed
- Set `APP_PUBLIC_URL` and `API_PUBLIC_URL` to real HTTPS URLs
- Set `MAIL_BACKEND=smtp` and configure the SMTP variables for real email delivery
- Confirm `CORS_ORIGINS` matches the public frontend origin
- Mount persistent storage for `/app/storage`
- Use HTTPS at the reverse proxy
- Keep `LOG_JSON=true` for production log aggregation

## Usage Limits and Fairness

- Free-tier usage is tracked per user in SQLite.
- Heavy tools consume more upload budget and queue weight.
- Queue ordering uses fair-share scoring so one user cannot easily dominate worker capacity.
- If the queue is full, the API returns a friendly `503` instead of hanging requests.

## Logging, Monitoring, and Admin

CreatorLab includes:

- `/health` and `/ready` endpoints
- structured logging support
- request logging middleware
- job failure logging
- admin summary metrics for:
  - recent jobs
  - failed jobs
  - queue depth
  - queue groups
  - storage usage
  - cleanup activity
  - active sessions
  - pending auth tokens
  - runtime and system stats

## Current Production-Ready vs Placeholder Areas

Implemented now:

- persistent jobs and history
- auth, verification, password reset
- local mail preview abstraction
- rembg with `u2net`
- Real-ESRGAN integration path with CPU/GPU detection
- retry-aware background workers
- Docker deployment structure

Still intentionally lightweight:

- payment checkout is Stripe-ready architecture only; no live billing provider is wired yet
- storage abstraction is designed for S3, but only local storage is implemented
- the mail abstraction is live with `local_file` and `smtp`; API-provider integrations such as Resend or Postmark can still be added later

## Development Workflow

Recommended loop:

1. Start the backend and frontend with `.\scripts\dev.ps1`
2. Make changes
3. Run `.\scripts\test.ps1`
4. Validate the target flow manually in the browser

For auth flow testing in local development:

1. Sign up with a new email
2. Open `GET /api/auth/dev/messages/latest?email=...&kind=verification`
3. Use the preview link or token
4. Request password reset from `/forgot-password`
5. Open `GET /api/auth/dev/messages/latest?email=...&kind=password_reset`
6. Complete `/reset-password`

## Notes for Solo Development

- The app is intentionally structured so you can keep shipping locally first and replace pieces later.
- Most externalized seams already exist: mail provider, billing provider, storage backend, and GPU-capable model runtime.
- The current API and UI are kept stable while these internals evolve.
