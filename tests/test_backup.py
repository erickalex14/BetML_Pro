import os
import subprocess
from datetime import datetime, timedelta

import pytest

from backend.pipeline import job_backup


def test_backup_invalido_no_borra_el_anterior(tmp_path, monkeypatch):
    anterior = tmp_path / "betml-anterior.dump"
    anterior.write_bytes(b"valido")
    fecha_vieja = (datetime.now() - timedelta(days=8)).timestamp()
    monkeypatch.setattr(job_backup, "BACKUP_DIR", tmp_path)
    monkeypatch.setenv("POSTGRES_PASSWORD", "test")

    def ejecutar(comando, **_kwargs):
        if comando[0] == "pg_dump":
            temporal = comando[comando.index("--file") + 1]
            open(temporal, "wb").close()
            return
        raise subprocess.CalledProcessError(1, comando)

    monkeypatch.setattr(job_backup.subprocess, "run", ejecutar)
    os.utime(anterior, (fecha_vieja, fecha_vieja))

    with pytest.raises(subprocess.CalledProcessError):
        job_backup.correr_backup()

    assert anterior.exists()
    assert not list(tmp_path.glob("*.tmp"))
