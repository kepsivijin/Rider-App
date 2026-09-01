#!/usr/bin/env bash
# Prints Render/Vercel env vars from backend/.env for dashboard copy-paste.
# Secrets stay local — .env is gitignored.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy .env.example and fill in Neon + Upstash URLs."
  exit 1
fi

get_env() {
  local key="$1"
  local default="${2:-}"
  local val
  val="$(grep -E "^${key}=" "$ENV_FILE" | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//')"
  echo "${val:-$default}"
}

DATABASE_URL="$(get_env DATABASE_URL)"
REDIS_URL="$(get_env REDIS_URL)"
JWT_SECRET_KEY="$(get_env JWT_SECRET_KEY "$(openssl rand -hex 32)")"
ALLOWED_ORIGINS="$(get_env ALLOWED_ORIGINS "https://YOUR-APP.vercel.app")"

cat <<EOF

=== Render environment variables (paste in dashboard) ===

DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
DEBUG=True
ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
GOOGLE_MAPS_API_KEY=
RAZORPAY_KEY_ID=dummy
RAZORPAY_KEY_SECRET=dummy
FCM_SERVER_KEY=dummy
SMS_API_KEY=dummy
SMS_SENDER_ID=RIDESH

=== Vercel environment variables (after Render deploy) ===

Replace YOUR-API with your Render URL (e.g. rider-app-api.onrender.com):

VITE_API_URL=https://YOUR-API.onrender.com/api/v1
VITE_WS_URL=https://YOUR-API.onrender.com
VITE_GOOGLE_MAPS_API_KEY=

EOF
