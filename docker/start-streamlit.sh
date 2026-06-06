#!/usr/bin/env sh
set -eu

HOST="${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}"
PORT="${STREAMLIT_PORT:-8501}"

exec python -m streamlit run streamlit_app.py \
  --server.address "$HOST" \
  --server.port "$PORT" \
  --server.headless true \
  --browser.gatherUsageStats false
