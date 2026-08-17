"""Migraciones idempotentes mínimas mientras el proyecto no usa Alembic."""
from sqlalchemy import text

from backend.db.database import engine


def aplicar_migraciones() -> None:
    if engine.dialect.name != "postgresql":
        return

    sentencias = (
        "ALTER TABLE usuarios ALTER COLUMN password_hash DROP NOT NULL",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS google_sub VARCHAR(64)",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre VARCHAR(120)",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email_verificado BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMP",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_google_sub ON usuarios (google_sub) WHERE google_sub IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS ix_partidos_fecha ON partidos (fecha)",
        "CREATE INDEX IF NOT EXISTS ix_partidos_estado ON partidos (estado)",
        "CREATE INDEX IF NOT EXISTS ix_partidos_liga_id ON partidos (liga_id)",
        "CREATE INDEX IF NOT EXISTS ix_partidos_equipo_local_id ON partidos (equipo_local_id)",
        "CREATE INDEX IF NOT EXISTS ix_partidos_equipo_visit_id ON partidos (equipo_visit_id)",
        "CREATE INDEX IF NOT EXISTS ix_partidos_equipo_local_fecha ON partidos (equipo_local_id, fecha)",
        "CREATE INDEX IF NOT EXISTS ix_partidos_equipo_visit_fecha ON partidos (equipo_visit_id, fecha)",
        "CREATE INDEX IF NOT EXISTS ix_odds_partido_id ON odds (partido_id)",
        "CREATE INDEX IF NOT EXISTS ix_predicciones_partido_id ON predicciones (partido_id)",
        "CREATE INDEX IF NOT EXISTS ix_estadisticas_jugador_partido_id ON estadisticas_jugador (partido_id)",
        "CREATE INDEX IF NOT EXISTS ix_estadisticas_jugador_equipo_id ON estadisticas_jugador (equipo_id)",
        "CREATE INDEX IF NOT EXISTS ix_estadisticas_jugador_sofascore_jugador_id ON estadisticas_jugador (sofascore_jugador_id)",
    )
    with engine.begin() as conexion:
        for sentencia in sentencias:
            conexion.execute(text(sentencia))
