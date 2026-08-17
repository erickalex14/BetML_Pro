import logging
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from backend.db.modelos import Partido, Equipo
from backend.repositories.partido_repo import PartidoRepository
from backend.repositories.prediccion_repo import PrediccionRepository
from backend.services.modelo_service import get_modelo_service
from backend.core.config import get_settings
from backend.features.calculador import construir_features_partido
from backend.features.dataset import FEATURES_ML as FEATURES
from backend.models.calibracion import cargar_calibracion, calibrar_probabilidades
from backend.models.explicacion import generar_resumen, generar_resumen_h2h
log = logging.getLogger(__name__)

class PrediccionService:
    """
    Este servicio orquesta el flujo completo de las predicciones
    """

    def __init__(self, db: Session):
        self.db = db
        self.partido_repo = PartidoRepository(db)
        self.prediccion_repo = PrediccionRepository(db)
        self.modelo_service = get_modelo_service()
        self.settings = get_settings()


    def predecir(self, partido: Partido, persistir: bool = False) -> dict | None:
        """persistir=True guarda la predicción para tracking de MLOps
        (ver job_cerrar_predicciones.py). False por default — Kelly,
        Monte Carlo y el resto de los endpoints llaman a predecir() como
        utilidad interna, potencialmente varias veces por partido; no
        cada llamada es "la predicción oficial del día". predecir_hoy()
        sí persiste — ese es el snapshot real a trackear."""
        features = construir_features_partido(self.db, partido)
        if features is None:
            return self._predecir_desde_mercado(partido, persistir)

        if not self.modelo_service.disponible:
            log.warning("Modelo no disponible")
            return None

        X   = pd.DataFrame([features])[FEATURES].fillna(0)
        proba = self.modelo_service.predecir_proba(X)[0]

        # Calibra — XGBoost no da probabilidades bien calibradas
        # (ver backend/models/calibracion.py). Kelly y el resto del
        # sistema deben ver la probabilidad calibrada, no la cruda.
        calibracion = cargar_calibracion()
        if calibracion is not None:
            proba = calibrar_probabilidades(calibracion, proba)

        # Una muestra general usada como fallback permite predecir, pero no
        # merece la misma certeza que cinco partidos en la localía exacta.
        # Encogemos hacia 1/3 manteniendo suma=1, en vez de ocultar el partido
        # o inventar features con cero.
        calidad_datos = features.get("calidad_datos", "alta")
        if calidad_datos == "moderada":
            proba = 0.85 * np.asarray(proba) + 0.15 * np.array([1 / 3] * 3)

        prob_local = round(float(proba[0]), 4)
        prob_empate = round(float(proba[1]), 4)
        prob_visit = round(float(proba[2]), 4)

        idx_max  = int(np.argmax(proba))
        labels   = ["Local", "Empate", "Visitante"]
        pred_label = labels[idx_max]
        confianza = round(float(proba[idx_max]), 4)

        mercados = self._generar_mercados(prob_local, prob_empate, prob_visit)

        factores, resumen_h2h = [], None
        importancias_arr = self.modelo_service.feature_importances
        if importancias_arr is not None:
            importancias = dict(zip(FEATURES, importancias_arr))
            factores = generar_resumen(
                features, importancias,
                partido.equipo_local.nombre, partido.equipo_visitante.nombre,
            )
            resumen_h2h = generar_resumen_h2h(
                features, partido.equipo_local.nombre, partido.equipo_visitante.nombre,
            )

        if persistir:
            self.prediccion_repo.crear(
                partido_id = partido.id,
                mercado = "1X2",
                prediccion = pred_label,
                probabilidad = confianza,
                confianza = confianza,
            )

        return {
            "partido_id": partido.id,
            "prob_local": prob_local,
            "prob_empate": prob_empate,
            "prob_visitante": prob_visit,
            "prediccion": pred_label,
            "confianza": confianza,
            "mercados_recomendados": mercados,
            "factores": factores,
            "resumen_h2h": resumen_h2h,
            "calidad_datos": calidad_datos,
            "origen_prediccion": "ml",
            "diagnostico_historial": features.get("diagnostico_historial"),
        }

    def _predecir_desde_mercado(self, partido: Partido,
                                persistir: bool = False) -> dict | None:
        from backend.models.odds_service import probabilidades_mercado_1x2

        probs = probabilidades_mercado_1x2(self.db, partido.id)
        if probs is None:
            log.warning(f"Sin historial ni cuotas 1X2 completas para partido {partido.id}")
            return None
        valores = [probs["prob_local"], probs["prob_empate"],
                   probs["prob_visitante"]]
        idx = int(np.argmax(valores))
        labels = ["Local", "Empate", "Visitante"]
        pred_label = labels[idx]
        confianza = valores[idx]
        if persistir:
            self.prediccion_repo.crear(
                partido_id=partido.id, mercado="1X2-mercado",
                prediccion=pred_label, probabilidad=confianza,
                confianza=confianza,
            )
        return {
            "partido_id": partido.id,
            **probs,
            "prediccion": pred_label,
            "confianza": confianza,
            "mercados_recomendados": self._generar_mercados(*valores),
            "factores": [{
                "factor": "Cuotas 1X2",
                "favorece": pred_label.lower(),
                "texto": "Estimación basada únicamente en probabilidades implícitas del mercado, sin margen.",
            }],
            "resumen_h2h": None,
            "calidad_datos": "solo_mercado",
            "origen_prediccion": "mercado",
            "diagnostico_historial": {
                "codigo": "MARKET_ONLY",
                "calidad": "solo_mercado",
            },
        }

    def predecir_en_vivo(self, partido: Partido, n_simulaciones: int = 8000) -> dict | None:
        """Recalcula 1X2 y mercados de gol EN VIVO dado el marcador y
        minuto actuales — no es un modelo nuevo entrenado aparte: escala
        el xG pre-partido (Sofascore si ya hay stats en vivo, si no la
        previsión histórica prepartido que /recomendadas) por el tiempo que
        falta, simula el resto del partido con Monte Carlo, y le suma el
        marcador ya jugado antes de calcular todo (ver goles_local_base/
        visit_base en montecarlo.simular_partido). None si el partido no
        está en juego o falta el minuto — ver estimar_fraccion_restante."""
        from backend.models.montecarlo import simular_partido, estimar_fraccion_restante

        fraccion = estimar_fraccion_restante(partido.estado, partido.minuto)
        if fraccion is None:
            return None

        pred = self.predecir(partido)
        if not pred:
            return None

        # xG esperado para el partido completo con información disponible
        # antes del inicio. La probabilidad de empate no debe reducir el
        # total esperado de goles.
        from backend.features.calculador import calcular_stats_sofascore
        from backend.features.medias_liga import medias_globales, estimar_xg_prepartido
        sf_local = calcular_stats_sofascore(
            self.db, partido.equipo_local_id, partido.fecha, es_local=True)
        sf_visit = calcular_stats_sofascore(
            self.db, partido.equipo_visit_id, partido.fecha, es_local=False)
        xg_local_pre, xg_visit_pre, fuente_pre = estimar_xg_prepartido(
            sf_local, sf_visit, medias_globales(self.db))

        # El xG de Sofascore en un partido EN CURSO es lo acumulado hasta
        # el minuto actual, no una previsión del partido entero. Tratarlo
        # como si fuera el total y encima multiplicarlo por el tiempo que
        # falta descuenta dos veces: en Cruzeiro-Flamengo, 0-0 al 48',
        # daba 0.18 y 0.25 de xG para los 42 minutos restantes (0.43
        # goles esperados en casi medio tiempo) y el empate se iba a 69%.
        # Lo correcto es extrapolar el ritmo mostrado a los 90 minutos.
        stats = partido.stats_sofascore
        minutos_jugados = max(1, 90 - int(fraccion * 90))
        if stats and stats.xg_local and stats.xg_visitante:
            ritmo_local = stats.xg_local * 90 / minutos_jugados
            ritmo_visit = stats.xg_visitante * 90 / minutos_jugados
            # Cuanto más partido va, más vale lo que se está viendo; al
            # principio, con 10 minutos jugados, el ritmo observado es
            # puro ruido y manda la previsión del modelo.
            peso_vivo = min(1.0, minutos_jugados / 90)
            xg_local_total = peso_vivo * ritmo_local + (1 - peso_vivo) * xg_local_pre
            xg_visit_total = peso_vivo * ritmo_visit + (1 - peso_vivo) * xg_visit_pre
            fuente = f"xG en vivo + {fuente_pre.lower()}"
        else:
            xg_local_total, xg_visit_total = xg_local_pre, xg_visit_pre
            fuente = fuente_pre

        goles_local_actual = partido.goles_local or 0
        goles_visit_actual = partido.goles_visitante or 0

        montecarlo = simular_partido(
            xg_local_total * fraccion, xg_visit_total * fraccion,
            n_simulaciones=n_simulaciones,
            goles_local_base=goles_local_actual,
            goles_visit_base=goles_visit_actual,
            incluir_handicap=True,
        )

        # Mercados que siguen vivos con el partido en curso. Las líneas de
        # goles se leen sobre el TOTAL del partido (el simulador ya suma
        # los goles hechos), así que "Over 2.5" con 2-0 al 60' es la
        # probabilidad real de que caiga uno más, no una línea teórica.
        ou = montecarlo["over_under"]
        mercados = []
        for linea in (0.5, 1.5, 2.5, 3.5, 4.5):
            clave = str(linea).replace(".", "_")
            for lado in ("over", "under"):
                prob = ou.get(f"{lado}_{clave}")
                if prob is None:
                    continue
                # las que ya se definieron solas no aportan nada
                if prob >= 0.995 or prob <= 0.005:
                    continue
                mercados.append({
                    "mercado": f"Goles {lado.capitalize()} {linea}",
                    "clave": f"goles_{lado}_{clave}",
                    "probabilidad": prob,
                })

        for nombre, clave in (("BTTS Sí", "btts_si"), ("BTTS No", "btts_no")):
            prob = montecarlo.get(clave)
            if prob is not None and 0.005 < prob < 0.995:
                mercados.append({"mercado": nombre, "clave": clave, "probabilidad": prob})

        for nombre, clave in (("Gana Local", "prob_local"), ("Empate", "prob_empate"),
                               ("Gana Visitante", "prob_visitante")):
            mercados.append({"mercado": nombre, "clave": clave.replace("prob_", ""),
                             "probabilidad": montecarlo[clave]})

        mercados.sort(key=lambda m: m["probabilidad"], reverse=True)

        return {
            "partido_id": partido.id,
            "estado": partido.estado,
            "minuto": partido.minuto,
            "marcador_actual": f"{goles_local_actual}-{goles_visit_actual}",
            "fraccion_restante": round(fraccion, 3),
            "fuente_xg": fuente,
            "prob_local": montecarlo["prob_local"],
            "prob_empate": montecarlo["prob_empate"],
            "prob_visitante": montecarlo["prob_visitante"],
            "goles_esperados_restantes": round(
                (xg_local_total + xg_visit_total) * fraccion, 2),
            "mercados": mercados,
            "montecarlo": montecarlo,
        }

    def _generar_mercados(self, prob_l: float,
                          prob_e: float,
                          prob_v: float) -> list[dict]:
        """
        Genera lista de mercados recomendados según
        las probabilidades del modelo.
        Solo recomienda si supera el umbral configurado.
        """
        umbral = self.settings.umbral_confianza
        mercados = []

        # 1X2
        for prob, label in [(prob_l, "Local"),
                            (prob_e, "Empate"),
                            (prob_v, "Visitante")]:
            if prob >= umbral:
                mercados.append({
                    "mercado": "1X2",
                    "seleccion": label,
                    "probabilidad": prob
                })

        # Doble oportunidad
        if (prob_l + prob_e) >= 0.75:
            mercados.append({
                "mercado": "Doble Oportunidad",
                "seleccion": "1X",
                "probabilidad": round(prob_l + prob_e, 4)
            })

        if (prob_v + prob_e) >= 0.75:
            mercados.append({
                "mercado": "Doble Oportunidad",
                "seleccion": "X2",
                "probabilidad": round(prob_v + prob_e, 4)
            })

        # Ordena por probabilidad descendente
        return sorted(mercados,
                      key=lambda x: x["probabilidad"],
                      reverse=True)


    #Predecir los partidos pendientes
    def predecir_hoy(self) -> list[dict]:
        from backend.pipeline.config import fecha_hoy_partidos
        partidos = self.partido_repo.get_por_fecha(fecha_hoy_partidos())
        resultados = []
        for p in partidos:
            if p.estado in ["NS", "TDB"]:
                pred = self.predecir(p, persistir=True)
                if pred:
                    resultados.append(pred)
        return resultados
