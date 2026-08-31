# Rider-App

FastAPI backend for Kanyakumari RideShare (Marthandam region).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_test_users.py
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

API docs: http://localhost:8001/docs

## Deploy (free)

- **Render** — web service, root = this repo
- **Neon** — PostgreSQL
- **Upstash** — Redis

```env
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
JWT_SECRET_KEY=...
DEBUG=True
ALLOWED_ORIGINS=https://YOUR-FRONTEND.vercel.app
```

Build: `pip install -r requirements.txt && alembic upgrade head`  
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
