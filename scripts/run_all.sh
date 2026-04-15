#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"

echo "Starting atlasd..."
python -m cmd.atlasd.main --config configs/policy.yaml &
ATLAS_PID=$!

echo "Waiting for /healthz..."
sleep 1
curl -sf http://127.0.0.1:8000/healthz >/dev/null

echo "Submitting smoke job..."
python tools/smoke_submit.py || true

echo "Done. Atlas pid=${ATLAS_PID}"
