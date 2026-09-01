# Deploy Backend (Render) — Free

Repo: https://github.com/kepsivijin/Rider-App

## Prerequisites (create these first)

### 1. Neon — PostgreSQL (free)

1. https://neon.tech → Sign up → New project `rideshare`
2. Copy connection string (must include `?sslmode=require`):
   ```
   postgresql://user:pass@ep-xxx.neon.tech/rideshare?sslmode=require
   ```

### 2. Upstash — Redis (free)

1. https://upstash.com → Create Redis database
2. Copy **Redis URL** (starts with `rediss://`)

---

## Deploy on Render

1. https://render.com → Sign in with GitHub
2. **New +** → **Blueprint** (uses `render.yaml`) **or** **Web Service**
3. Connect repo: **kepsivijin/Rider-App**
4. If manual setup (no Blueprint):
   - **Root directory:** *(leave blank — repo root is backend)*
   - **Runtime:** Python 3
   - **Build command:**
     ```bash
     pip install -r requirements.txt && alembic upgrade head
     ```
   - **Start command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Health check path:** `/health`

### Environment variables

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Neon connection string |
| `REDIS_URL` | Upstash `rediss://...` URL |
| `JWT_SECRET_KEY` | Long random string (e.g. `openssl rand -hex 32`) |
| `DEBUG` | `True` (demo OTP `123456` on screen) |
| `ALLOWED_ORIGINS` | `https://YOUR-APP.vercel.app` (update after Vercel deploy) |
| `GOOGLE_MAPS_API_KEY` | *(empty — app uses OpenStreetMap)* |
| `RAZORPAY_KEY_ID` | `dummy` |
| `RAZORPAY_KEY_SECRET` | `dummy` |
| `FCM_SERVER_KEY` | `dummy` |
| `SMS_API_KEY` | `dummy` |

5. Click **Create Web Service** → wait for deploy (~3–5 min)
6. Note your API URL: `https://rider-app-api.onrender.com` (or similar)

### Seed demo users (one time)

Render dashboard → your service → **Shell**:

```bash
python scripts/seed_test_users.py
```

Or locally (with Neon `DATABASE_URL` in `.env`):

```bash
pip install -r requirements.txt
python scripts/seed_test_users.py
```

---

## Verify

```bash
curl https://YOUR-API.onrender.com/health
# {"status":"healthy"}

curl https://YOUR-API.onrender.com/
# {"message":"Kanyakumari RideShare API",...}
```

API docs: `https://YOUR-API.onrender.com/docs`

---

## Notes

- **Free tier sleeps** after ~15 min idle; first request may take 30–60s
- After Vercel deploy, update `ALLOWED_ORIGINS` with the real frontend URL and redeploy
- Demo logins: Customer `9876543210`, Driver `9876543212`, Admin `9876543213` — OTP `123456`
