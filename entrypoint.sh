#!/bin/sh
set -e

# wait for the database to accept connections before running migrations.
# `depends_on` in docker-compose only waits for the container to start, not
# for the service port to be ready.

echo "[entrypoint] waiting for database to become available..."
until python - <<'PYTHON'
import os
from sqlalchemy import create_engine

url = os.environ.get('DATABASE_URL')
if not url:
    raise RuntimeError('DATABASE_URL not set')

try:
    engine = create_engine(url)
    with engine.connect():
        pass
    # connection succeeded
    import sys
    sys.exit(0)
except Exception:
    import sys
    sys.exit(1)
PYTHON
do
    echo "[entrypoint] database not ready yet, sleeping 1s..."
    sleep 1
done

echo "[entrypoint] database is available, running migrations..."

alembic revision --autogenerate -m "initial schema"
alembic upgrade head

echo "[entrypoint] migrations complete, starting application"

exec "$@"
