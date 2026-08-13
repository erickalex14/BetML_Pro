"""Cuotas desde Sofascore — reemplazo gratis de job_odds.py.

Motivo: el plan free de API-Football son 100 requests/día y las cuotas
se llevaban hasta 20 (1 por partido). Sofascore no cobra por request, y
publica las cuotas de bet365 por evento. Mientras la app no se pague
sola el plan pro, las cuotas salen de acá y API-Football queda para lo
que Sofascore no da.

Endpoint: /event/{id}/odds/1/all (el "1" es el id del proveedor,
bet365 — sale de /odds/providers/{pais}/web-odds). Sacado del tráfico
real de sofascore.com, no adivinado.

Ojo con dos cosas del formato:
  - Las cuotas vienen FRACCIONARIAS ("1/5", "19/4"), no decimales. Hay
    que convertir: decimal = numerador/denominador + 1.
  - La línea (2.5 goles, 9.5 córners, hándicap) va en "choiceGroup",
    no en el nombre de la opción como en API-Football.

Solo se mapean los mercados que el modelo sabe analizar. Los que
Sofascore trae y no usamos (Double chance, Draw no bet, First team to
score) se ignoran a propósito.

Requiere sofascore_id anclado (ver job_alineaciones.py): sin eso no hay
evento que consultar.
"""
import logging
from datetime import timedelta

from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, Odds
from backend.pipeline.config import ahora_partidos

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

BOOKMAKER = "sofascore-bet365"
PROVEEDOR = 1  # bet365


def _a_decimal(fraccional: str) -> float | None:
    """"1/5" -> 1.20, "19/4" -> 5.75, "9/1" -> 10.0"""
    if not fraccional or "/" not in fraccional:
        return None
    try:
        num, den = fraccional.split("/", 1)
        den = float(den)
        if den == 0:
            return None
        return round(float(num) / den + 1, 3)
    except (ValueError, TypeError):
        return None


def _linea_a_clave(texto: str) -> str:
    """'2.5' -> '2_5', '-1.5' -> 'm1_5' (mismo formato que montecarlo.py
    y job_odds.py, para que las claves sean intercambiables)."""
    return str(texto).strip().lstrip("+").replace(".", "_").replace("-", "m")


def parsear_mercados(mercados: list) -> dict:
    """De la respuesta de Sofascore a las claves odds_* que usa kelly.py."""
    salida = {}

    for m in mercados:
        if m.get("suspended"):
            continue
        nombre = m.get("marketName", "")
        grupo = m.get("choiceGroup")
        opciones = {c.get("name"): _a_decimal(c.get("fractionalValue"))
                    for c in m.get("choices", [])}

        if nombre == "Full time":
            for opcion, clave in (("1", "odds_local"), ("X", "odds_empate"), ("2", "odds_visitante")):
                if opciones.get(opcion):
                    salida[clave] = opciones[opcion]

        elif nombre == "1st half":
            for opcion, clave in (("1", "odds_1t_local"), ("X", "odds_1t_empate"), ("2", "odds_1t_visitante")):
                if opciones.get(opcion):
                    salida[clave] = opciones[opcion]

        elif nombre == "Both teams to score":
            if opciones.get("Yes"):
                salida["odds_btts_si"] = opciones["Yes"]
            if opciones.get("No"):
                salida["odds_btts_no"] = opciones["No"]

        elif nombre in ("Match goals", "Corners 2-Way") and grupo:
            prefijo = "goles" if nombre == "Match goals" else "corners"
            linea = _linea_a_clave(grupo)
            for opcion, lado in (("Over", "over"), ("Under", "under")):
                if opciones.get(opcion):
                    salida[f"odds_{prefijo}_{lado}_{linea}"] = opciones[opcion]

        elif nombre == "Asian handicap" and grupo:
            # el grupo trae la línea del LOCAL ("-1.5"); la del visitante
            # es la simétrica, igual que en job_odds.py
            linea = _linea_a_clave(grupo)
            if opciones.get("1"):
                salida[f"odds_handicap_local_{linea}"] = opciones["1"]
            if opciones.get("2"):
                try:
                    inversa = _linea_a_clave(str(-float(grupo)))
                    salida[f"odds_handicap_visit_{inversa}"] = opciones["2"]
                except ValueError:
                    pass

    return salida


def _partidos_a_cotizar(db, dias_adelante: int = 2) -> list:
    ahora = ahora_partidos()
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Partido)
        .filter(
            Partido.sofascore_id.isnot(None),
            Partido.estado.in_(["NS", "TBD"]),
            Partido.fecha >= inicio,
            Partido.fecha <= inicio + timedelta(days=dias_adelante),
        )
        .order_by(Partido.fecha)
        .all()
    )


def correr_job_odds_sofascore():
    log.info("=" * 55)
    log.info("  Cuotas desde Sofascore (sin gastar API-Football)")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    con_cuotas = mercados_guardados = 0

    try:
        partidos = _partidos_a_cotizar(db)
        if not partidos:
            log.info("Sin partidos por cotizar")
            return 0

        from backend.pipeline.sofascore.cliente import SofascoreCliente
        log.info(f"{len(partidos)} partido(s) por cotizar")

        with SofascoreCliente() as cliente:
            for partido in partidos:
                data = cliente.get(f"/event/{partido.sofascore_id}/odds/{PROVEEDOR}/all")
                if not data:
                    continue
                mercados = parsear_mercados(data.get("markets", []))
                if not mercados:
                    continue

                # se reemplazan las de este proveedor; las de otros
                # (API-Football) quedan, obtener_mejores_odds se queda
                # con la mejor de todas
                db.query(Odds).filter(
                    Odds.partido_id == partido.id, Odds.bookmaker == BOOKMAKER
                ).delete()
                for clave, valor in mercados.items():
                    db.add(Odds(partido_id=partido.id, bookmaker=BOOKMAKER,
                                mercado=clave, valor=valor))
                    mercados_guardados += 1
                db.commit()
                con_cuotas += 1

        log.info(f"Partidos con cuotas: {con_cuotas} | filas guardadas: {mercados_guardados}")
    except Exception as e:
        log.error(f"Error en cuotas Sofascore: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return con_cuotas


if __name__ == "__main__":
    correr_job_odds_sofascore()
