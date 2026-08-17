from datetime import datetime, timedelta

from backend.db.database import SessionLocal
from backend.db.modelos import Equipo, Partido
from backend.features.calculador import (
    construir_features_partido,
    diagnosticar_historial,
)


def test_fallback_general_cubre_muestra_de_localia_sin_fuga_temporal():
    db = SessionLocal()
    fecha_objetivo = datetime(2026, 8, 20, 18, 0)
    ids = [8101, 8102, 8103, 8104]
    partido_ids = [98101, 98102, 98103, 98104, 98105, 98106, 98107, 98108]
    try:
        db.query(Partido).filter(Partido.id.in_(partido_ids)).delete(
            synchronize_session=False
        )
        db.query(Equipo).filter(Equipo.id.in_(ids)).delete(
            synchronize_session=False
        )
        db.add_all(
            [Equipo(id=i, nombre=f"Equipo calidad {i}", pais="Test") for i in ids]
        )

        # El futuro local solo jugo como visitante; el futuro visitante,
        # solo como local. Hay historia real suficiente, pero no en el rol.
        for n in range(3):
            db.add(
                Partido(
                    id=98101 + n,
                    liga_id=39,
                    temporada=2026,
                    equipo_local_id=8103,
                    equipo_visit_id=8101,
                    fecha=fecha_objetivo - timedelta(days=10 - n),
                    estado="FT",
                    goles_local=0,
                    goles_visitante=2,
                )
            )
            db.add(
                Partido(
                    id=98104 + n,
                    liga_id=39,
                    temporada=2026,
                    equipo_local_id=8102,
                    equipo_visit_id=8104,
                    fecha=fecha_objetivo - timedelta(days=7 - n),
                    estado="FT",
                    goles_local=1,
                    goles_visitante=1,
                )
            )
        objetivo = Partido(
            id=98107,
            liga_id=39,
            temporada=2026,
            equipo_local_id=8101,
            equipo_visit_id=8102,
            fecha=fecha_objetivo,
            estado="NS",
        )
        db.add(objetivo)
        # Este 9-0 no puede contaminar features del partido objetivo.
        db.add(
            Partido(
                id=98108,
                liga_id=39,
                temporada=2026,
                equipo_local_id=8101,
                equipo_visit_id=8102,
                fecha=fecha_objetivo + timedelta(days=1),
                estado="FT",
                goles_local=9,
                goles_visitante=0,
            )
        )
        db.commit()

        diagnostico = diagnosticar_historial(db, objetivo)
        features = construir_features_partido(db, objetivo)

        assert diagnostico["codigo"] == "INSUFFICIENT_VENUE_SAMPLE"
        assert diagnostico["calidad"] == "moderada"
        assert diagnostico["local_partidos_localia"] == 0
        assert diagnostico["visitante_partidos_localia"] == 0
        assert features is not None
        assert features["forma_local_puntos"] == 9
        assert features["forma_local_gf"] == 2.0
        assert features["forma_visit_puntos"] == 3
        assert features["calidad_datos"] == "moderada"
    finally:
        db.rollback()
        db.query(Partido).filter(Partido.id.in_(partido_ids)).delete(
            synchronize_session=False
        )
        db.query(Equipo).filter(Equipo.id.in_(ids)).delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


def test_sin_tres_partidos_generales_sigue_bloqueando_prediccion():
    db = SessionLocal()
    try:
        partido = db.get(Partido, 900001)
        diagnostico = diagnosticar_historial(db, partido)

        assert diagnostico["codigo"] == "NO_FINISHED_MATCHES"
        assert diagnostico["calidad"] == "insuficiente"
        assert construir_features_partido(db, partido) is None
    finally:
        db.close()
