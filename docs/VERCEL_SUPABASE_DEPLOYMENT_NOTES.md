# Vercel & Supabase Deployment Notes

This document provides guidelines for deploying the MediPlatform architecture using Vercel (for the frontend applications) and Supabase (as the managed PostgreSQL backend).

## Architecture Overview

- **Database**: Supabase (Managed PostgreSQL)
- **Backend**: FastAPI (Deployed via Vercel Serverless Functions or a dedicated platform like Render/Railway)
- **Frontend**: Next.js (Patient Kiosk & Doctor Dashboard deployed on Vercel)

## Supabase PostgreSQL Configuration

### 1. Database Connection
Supabase provides two connection types:
- **Session Mode (Port 5432)**: Direct connection for long-running processes.
- **Transaction Mode (Port 6543)**: Connection pooling via PgBouncer, required for Serverless deployments like Vercel and AWS Lambda.

**Important**: FastAPI running in a serverless environment or any heavily concurrent environment should use the **Transaction Mode (6543)** connection string to avoid connection limit exhaustion.

### 2. SQLAlchemy Settings
When connecting to Supabase via PgBouncer (Port 6543), SQLAlchemy connection pooling must be disabled. Use `NullPool` to let PgBouncer handle pooling:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool
)
```

## Vercel Deployment

### Environment Variables

Ensure the following variables are configured in the Vercel project settings:

**Backend (if deployed on Vercel via Serverless):**
- `DATABASE_URL`: Your Supabase connection string (using port 6543)
- `AI_MODE`: `mock` (or actual API keys when implementing real AI)
- `CORS_ORIGINS`: Comma-separated list of your Vercel frontend domains

**Frontend (Patient Kiosk / Doctor Dashboard):**
- `NEXT_PUBLIC_API_URL`: URL of the deployed FastAPI backend.
- `NEXT_PUBLIC_DATA_MODE`: `api` (Ensure this is set to `api` rather than `mock` for production builds to connect to the backend).

### Next.js Configuration
The Next.js applications (`patient-kiosk` and `doctor-dashboard`) should be deployed as separate Vercel projects. 
- **Root Directory**: Select `frontend/patient-kiosk` or `frontend/doctor-dashboard` during Vercel project setup.
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

## Migrations

Alembic must be executed from a dedicated CI/CD runner or locally before launching the new version, as serverless functions should not run migrations on startup.
Always run `alembic upgrade head` carefully against the production Supabase project. Make sure you back up production data before running complex migrations.
