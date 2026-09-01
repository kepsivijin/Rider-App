#!/usr/bin/env bash
# Deploy backend to Render via CLI (requires RENDER_API_KEY in environment).
set -euo pipefail

if [[ -z "${RENDER_API_KEY:-}" ]]; then
  echo "Set RENDER_API_KEY first (Render Dashboard → Account Settings → API Keys)"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
get_env() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//'; }

export CI=true
DATABASE_URL="$(get_env DATABASE_URL)"
REDIS_URL="$(get_env REDIS_URL)"
JWT_SECRET_KEY="$(get_env JWT_SECRET_KEY)"
ALLOWED_ORIGINS="$(get_env ALLOWED_ORIGINS "https://rider-app-frontend.vercel.app")"

render services create \
  --name rider-app-api \
  --type web_service \
  --repo https://github.com/kepsivijin/Rider-App \
  --branch main \
  --runtime python \
  --plan free \
  --region singapore \
  --build-command "pip install -r requirements.txt && alembic upgrade head && python scripts/seed_test_users.py" \
  --start-command "uvicorn app.main:app --host 0.0.0.0 --port \$PORT" \
  --health-check-path /health \
  --env-var "DATABASE_URL=${DATABASE_URL}" \
  --env-var "REDIS_URL=${REDIS_URL}" \
  --env-var "JWT_SECRET_KEY=${JWT_SECRET_KEY}" \
  --env-var "DEBUG=True" \
  --env-var "ALLOWED_ORIGINS=${ALLOWED_ORIGINS}" \
  --env-var "GOOGLE_MAPS_API_KEY=" \
  --env-var "RAZORPAY_KEY_ID=dummy" \
  --env-var "RAZORPAY_KEY_SECRET=dummy" \
  --env-var "FCM_SERVER_KEY=dummy" \
  --env-var "SMS_API_KEY=dummy" \
  --env-var "SMS_SENDER_ID=RIDESH" \
  --output json \
  --confirm

echo "Backend deploy triggered. URL: https://rider-app-api.onrender.com"
