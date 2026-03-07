#!/bin/sh
set -e

echo "Applying database migrations"
alembic upgrade head

if [ "${SEED_DEMO:-false}" = "true" ]; then
  python -m timesheets.seed
fi

exec "$@"
