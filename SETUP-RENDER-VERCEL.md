# Render + Vercel setup (step-by-step)

Your Neon DB and Upstash Redis are already working locally. Follow these steps in order.

**Repos:**
- Backend: https://github.com/kepsivijin/Rider-App
- Frontend: https://github.com/kepsivijin/Rider-app-Frontend

---

## Step 1 — Render (backend API)

### Option A — Blueprint (recommended, uses `render.yaml`)

1. Open: https://dashboard.render.com/blueprints
2. Click **New Blueprint Instance**
3. Connect **GitHub** if not connected → authorize Render
4. Select repo: **kepsivijin/Rider-App**
5. Render reads `render.yaml` and asks for **4 secret values**. Paste:

| Variable | Where to get it |
|----------|-----------------|
| `DATABASE_URL` | Neon dashboard → Connection string (pooler) |
| `REDIS_URL` | Upstash → Redis URL as `rediss://default:TOKEN@HOST:6379` |
| `JWT_SECRET_KEY` | Any long random string (e.g. run `openssl rand -hex 32`) |
| `ALLOWED_ORIGINS` | `https://rider-app-frontend.vercel.app` *(use this now; update if Vercel URL differs)* |

6. Click **Apply** → wait ~5–10 min for first deploy
7. Your API URL: **https://rider-app-api.onrender.com**
8. Test: open https://rider-app-api.onrender.com/health → should show `{"status":"healthy"}`

> Build runs migrations + seeds demo users automatically.

### Option B — Manual Web Service

1. Open: https://dashboard.render.com/web/new
2. **Connect repository** → **kepsivijin/Rider-App**
3. Fill in:

| Field | Value |
|-------|-------|
| Name | `rider-app-api` |
| Region | **Singapore** |
| Branch | `main` |
| Runtime | **Python 3** |
| Build Command | `pip install -r requirements.txt && alembic upgrade head && python scripts/seed_test_users.py` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | **Free** |

4. **Advanced** → Health Check Path: `/health`
5. Add **Environment Variables** (same 4 secrets as Option A, plus these auto-set in render.yaml):
   - `DEBUG` = `True`
   - `RAZORPAY_KEY_ID` = `dummy`
   - `RAZORPAY_KEY_SECRET` = `dummy`
   - `FCM_SERVER_KEY` = `dummy`
   - `SMS_API_KEY` = `dummy`
6. **Create Web Service**

---

## Step 2 — Vercel (frontend)

1. Open: https://vercel.com/new
2. **Import Git Repository** → **kepsivijin/Rider-app-Frontend**
3. Vercel auto-detects **Vite**. Confirm:

| Field | Value |
|-------|-------|
| Framework Preset | Vite |
| Root Directory | `./` *(leave default)* |
| Build Command | `npm run build` |
| Output Directory | `dist` |

4. Expand **Environment Variables** and add:

| Name | Value |
|------|-------|
| `VITE_API_URL` | `https://rider-app-api.onrender.com/api/v1` |
| `VITE_WS_URL` | `https://rider-app-api.onrender.com` |
| `VITE_GOOGLE_MAPS_API_KEY` | *(leave empty)* |

5. Click **Deploy** → wait ~2 min
6. Your app URL: e.g. **https://rider-app-frontend.vercel.app**

---

## Step 3 — Connect CORS (important)

If your Vercel URL is **not** exactly `https://rider-app-frontend.vercel.app`:

1. Render → **rider-app-api** → **Environment**
2. Edit `ALLOWED_ORIGINS` → paste your **exact** Vercel URL (no trailing slash)
3. **Save Changes** → Render redeploys (~2 min)

---

## Step 4 — Test live demo

Open your Vercel URL:

| Role | Phone | OTP |
|------|-------|-----|
| Customer | `9876543210` | `123456` |
| Driver | `9876543212` | `123456` |
| Admin | `9876543213` | `123456` |

Tap **Send OTP** → OTP `123456` appears on screen.

**Note:** First API call after ~15 min idle may take 30–60 seconds (Render free tier wake-up).

---

## Quick links

| Service | Dashboard |
|---------|-----------|
| Render backend | https://dashboard.render.com |
| Vercel frontend | https://vercel.com/dashboard |
| Neon DB | https://console.neon.tech |
| Upstash Redis | https://console.upstash.com |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Login fails / CORS error | `ALLOWED_ORIGINS` on Render must match Vercel URL exactly |
| API timeout on first load | Wait 60s — Render free tier waking up |
| OTP not working | Ensure `DEBUG=True` on Render |
| 502 on Render | Check **Logs** tab — usually missing env var |

---

## Local env values (do NOT commit)

Run locally to print your values for copy-paste into Render dashboard:

```bash
cd backend && ./scripts/print-deploy-env.sh
```

`.env` is gitignored — secrets stay out of GitHub.
