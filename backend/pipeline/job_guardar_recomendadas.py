"""Guarda las apuestas recomendadas del día para que se cierren solas
contra el resultado real.

Sin esto las recomendadas eran efímeras: se calculaban al abrir la
pantalla y nadie registraba si acertaron. Ahora quedan como
Predicciones, así que job_cerrar_predicciones.py las marca
acertada/fallada cuando termina el partido, aparecen en /stats/modelo
con su accuracy por mercado, y alimentan la calibración de producción
(calibracion_produccion.py) — que es la parte de "aprender de sus
propios errores": si el sistema viene declarando 85% en un mercado
donde acierta 27%, esa curva lo detecta y corrige la probabilidad.

Corre una vez por día (después de que estén las cuotas), no en cada
request: la pantalla de recomendadas se abre muchas veces y guardar en
cada apertura llenaría la tabla de duplicados. Igual hay guardia de
duplicado por (partido, mercado) por las dudas.
"""
import logging
from datetime import date

from backend.db.database import SessionLocal
from backend.db.modelos import Prediccion

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def _ya_guardada(db, partido_id: int, mercado: str) -> bool:
    return (
        db.query(Prediccion)
        .filter(Prediccion.partido_id == partido_id, Prediccion.mercado == mercado)
        .first()
        is not None
    )


def correr_job_guardar_recomendadas():
    from backend.api.routes.predicciones import predicciones_recomendadas

    log.info("=" * 55)
    log.info("  Guardando recomendadas del día para tracking")
    log.info("=" * 55)

    db = SessionLocal()
    guardadas = 0
    try:
        datos = predicciones_recomendadas(db=db)

        # Solo las individuales: las combinadas y parlays son productos
        # de estas mismas patas, guardarlas otra vez contaría el mismo
        # acierto dos veces y ensuciaría la accuracy.
        individuales = (datos["apuestas_individuales"]["fijas"]
                        + datos["apuestas_individuales"]["sonadoras"])

        for apuesta in individuales:
            if _ya_guardada(db, apuesta["partido_id"], apuesta["clave"]):
                continue
            db.add(Prediccion(
                partido_id=apuesta["partido_id"],
                mercado=apuesta["clave"],
                prediccion=apuesta["mercado"],
                probabilidad=apuesta["probabilidad"],
                confianza=apuesta["probabilidad"],
            ))
            guardadas += 1

        db.commit()
        log.info(f"Recomendadas guardadas para seguimiento: {guardadas} "
                 f"(de {len(individuales)} sugeridas hoy, {date.today()})")
    except Exception as e:
        log.error(f"Error guardando recomendadas: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return guardadas


if __name__ == "__main__":
    correr_job_guardar_recomendadas()
