#!/bin/sh
set -e

echo "[entrypoint] waiting for postgres..."
python - << 'PY'
import time, sys
from sqlalchemy import create_engine
from app.config import get_settings

s = get_settings()
for i in range(30):
    try:
        create_engine(s.database_url).connect().close()
        print("db is up")
        sys.exit(0)
    except Exception as e:
        print(f"waiting... ({e})")
        time.sleep(1)
sys.exit(1)
PY

echo "[entrypoint] running migrations..."
alembic upgrade head

echo "[entrypoint] seeding..."
python -m app.seed

echo "[entrypoint] starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
