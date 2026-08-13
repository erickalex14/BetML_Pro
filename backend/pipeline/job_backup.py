import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


BACKUP_DIR = Path(os.getenv("BETML_BACKUP_DIR", "/app/backups"))
RETENTION_DAYS = 7


def correr_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    final = BACKUP_DIR / f"betml-{datetime.now():%Y%m%d-%H%M%S}.dump"
    temporal = final.with_suffix(".dump.tmp")
    env = os.environ.copy()
    env["PGPASSWORD"] = env["POSTGRES_PASSWORD"]
    conexion = [
        "--host", env.get("POSTGRES_HOST", "betml-db"),
        "--port", env.get("POSTGRES_PORT", "5432"),
        "--username", env.get("POSTGRES_USER", "betml"),
        "--dbname", env.get("POSTGRES_DB", "betml"),
    ]

    try:
        subprocess.run(
            ["pg_dump", "--format=custom", "--file", str(temporal), *conexion],
            check=True,
            env=env,
        )
        subprocess.run(
            ["pg_restore", "--list", str(temporal)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        temporal.replace(final)
    except Exception:
        temporal.unlink(missing_ok=True)
        raise

    limite = datetime.now() - timedelta(days=RETENTION_DAYS)
    for dump in BACKUP_DIR.glob("betml-*.dump"):
        if datetime.fromtimestamp(dump.stat().st_mtime) < limite:
            dump.unlink()
    return final
