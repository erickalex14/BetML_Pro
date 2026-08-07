"""Cierra el loop de MLOps — para cada Prediccion y cada ParlaySeleccion
sin resolver cuyo partido ya terminó, calcula si acertó contra el
resultado real (resolver_mercado.py entiende cualquier mercado: 1X2,
goles O/U, BTTS, corners, tarjetas, rojas, hándicap, 1er/2do tiempo).

Un Parlay se cierra solo cuando TODAS sus patas están resueltas —
acerto = AND de todas (si alguna pierde, el combinado entero pierde,
aunque las demás patas todavía no se hayan jugado no importa si ya hay
una perdida confirmada... salvo que se quiera cerrar apenas se sepa que
ya perdió; acá se espera a que todas terminen para simplificar, ver
nota en _cerrar_parlays_pendientes).
"""
import logging
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Prediccion, Partido, ParlaySeleccion, Parlay
from backend.repositories.prediccion_repo import PrediccionRepository
from backend.models.resolver_mercado import resolver_mercado

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def _clave_mercado(fila) -> str:
    """1X2/1X2-ensemble guardan la predicción como label ("Local") —
    resolver_mercado usa la clave en minúscula ("local"). El resto de
    los mercados ya guarda la clave interna directo en fila.mercado."""
    if fila.mercado in ("1X2", "1X2-ensemble"):
        return fila.prediccion.lower()
    return fila.mercado


def _cerrar_predicciones_individuales(db, repo: PrediccionRepository) -> int:
    pendientes = (
        db.query(Prediccion)
        .join(Partido, Partido.id == Prediccion.partido_id)
        .filter(Prediccion.resultado_real.is_(None), Partido.estado == "FT")
        .all()
    )

    cerradas = 0
    for fila in pendientes:
        partido = db.get(Partido, fila.partido_id)
        gano = resolver_mercado(db, partido, _clave_mercado(fila))
        if gano is None:
            continue  # falta stat (corners/HT) o fue push — se reintenta después

        if fila.mercado in ("1X2", "1X2-ensemble"):
            gl, gv = partido.goles_local, partido.goles_visitante
            texto = "Local" if gl > gv else ("Empate" if gl == gv else "Visitante")
        else:
            texto = "Ganó" if gano else "Perdió"

        repo.cerrar_prediccion(fila.id, gano, texto)
        cerradas += 1

    return cerradas


def _cerrar_parlays_pendientes(db) -> int:
    """Resuelve cada pata individualmente; el Parlay se cierra recién
    cuando TODAS sus patas tienen acerto != None (todos los partidos ya
    terminaron). No cierra en cuanto UNA pata pierde — es más simple y
    el resultado final es el mismo (esperar no cambia el acerto), solo
    tarda hasta que jueguen todos los partidos de la combinada."""
    parlays_pendientes = db.query(Parlay).filter(Parlay.acerto.is_(None)).all()
    cerrados = 0

    for parlay in parlays_pendientes:
        selecciones = (
            db.query(ParlaySeleccion).filter(ParlaySeleccion.parlay_id == parlay.id).all()
        )

        for sel in selecciones:
            if sel.acerto is not None:
                continue
            partido = db.get(Partido, sel.partido_id)
            gano = resolver_mercado(db, partido, sel.mercado)
            if gano is not None:
                sel.acerto = gano

        if all(s.acerto is not None for s in selecciones):
            parlay.acerto = all(s.acerto for s in selecciones)
            cerrados += 1

        db.commit()

    return cerrados


def correr_job_cerrar_predicciones():
    log.info("=" * 55)
    log.info("  Job Cerrar Predicciones — MLOps tracking")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    repo = PrediccionRepository(db)
    cerradas = parlays_cerrados = 0

    try:
        cerradas = _cerrar_predicciones_individuales(db, repo)
        parlays_cerrados = _cerrar_parlays_pendientes(db)
    except Exception as e:
        log.error(f"Error cerrando predicciones: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info(f"Predicciones individuales cerradas: {cerradas}")
        log.info(f"Parlays cerrados: {parlays_cerrados}")
        log.info("=" * 55)


if __name__ == "__main__":
    correr_job_cerrar_predicciones()
