#!/usr/bin/env sh
set -eu

echo "[entrypoint] waiting for database and running migrations..."
i=0
max_attempts=30
migrated=0
ALEMBIC_BIN="/app/.venv/bin/alembic"
PY_BIN="/app/.venv/bin/python"
UVICORN_BIN="/app/.venv/bin/uvicorn"
until [ "$i" -ge "$max_attempts" ]
do
  if "$ALEMBIC_BIN" upgrade head >/tmp/alembic.log 2>&1; then
    echo "[entrypoint] migrations applied"
    migrated=1
    break
  fi

  # Legacy bootstrap:
  # If tables exist but alembic_version does not, baseline to head and continue.
  if "$PY_BIN" - <<'PY' >/tmp/alembic-bootstrap.log 2>&1
import asyncio
import os
import asyncpg

async def main():
    db_url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = await asyncpg.connect(db_url)
    has_alembic = await conn.fetchval("select to_regclass('public.alembic_version') is not null")
    has_users = await conn.fetchval("select to_regclass('public.users') is not null")
    await conn.close()
    print("STAMP" if (not has_alembic and has_users) else "NOOP")

asyncio.run(main())
PY
  then
    if grep -q "STAMP" /tmp/alembic-bootstrap.log; then
      echo "[entrypoint] detected legacy schema without alembic_version, stamping to head..."
      "$ALEMBIC_BIN" stamp head >/tmp/alembic-stamp.log 2>&1 || true
      if "$ALEMBIC_BIN" upgrade head >/tmp/alembic.log 2>&1; then
        echo "[entrypoint] migrations applied after stamping"
        migrated=1
        break
      fi
    fi
  fi

  i=$((i + 1))
  echo "[entrypoint] migration attempt $i/$max_attempts failed, retrying in 2s..."
  sleep 2
done

if [ "$migrated" -ne 1 ]; then
  echo "[entrypoint] failed to apply migrations after $max_attempts attempts"
  cat /tmp/alembic.log || true
  cat /tmp/alembic-bootstrap.log || true
  cat /tmp/alembic-stamp.log || true
  exit 1
fi

# Safety fix for historical schema drift in legacy databases.
"$PY_BIN" - <<'PY' >/tmp/scopes-fix.log 2>&1 || true
import asyncio
import os
import asyncpg

async def main():
    db_url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = await asyncpg.connect(db_url)
    # Ensure columns introduced in later revisions exist.
    await conn.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_encrypted VARCHAR(500)")
    await conn.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS allowed_tags JSON NOT NULL DEFAULT '[]'::json")

    # Keep old deployments compatible with current ORM (JSON scopes).
    typ = await conn.fetchval("""
        select c.udt_name
        from information_schema.columns c
        where c.table_schema='public' and c.table_name='api_keys' and c.column_name='scopes'
    """)
    if typ == "_varchar":
        await conn.execute("""
            alter table api_keys
            alter column scopes type json
            using array_to_json(coalesce(scopes, array[]::varchar[]))
        """)
        print("converted api_keys.scopes to json")
    await conn.close()

asyncio.run(main())
PY

exec "$UVICORN_BIN" app.main:app --host 0.0.0.0 --port 8000
