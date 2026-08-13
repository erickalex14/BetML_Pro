from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from backend.db.modelos import Prediccion, Parlay

class PrediccionRepository:
    def __init__(self, db: Session):
        self.db = db

    #Crear una prediccion
    def crear(self, partido_id: int, mercado: str,
              prediccion: str, probabilidad: float,
              confianza: float, usuario_id: int | None = None) -> Prediccion:
        """usuario_id=None significa "la generó el sistema" — ver el
        docstring de Prediccion."""

        pred = Prediccion(
            usuario_id=usuario_id,
            partido_id=partido_id,
            mercado=mercado,
            prediccion=prediccion,
            probabilidad=probabilidad,
            confianza=confianza
        )
        self.db.add(pred)
        self.db.commit()
        self.db.refresh(pred)
        return pred

    #Obtener predicciones por partido
    def get_por_partido(self, partido_id: int) -> List[Prediccion]:
        return (
            self.db.query(Prediccion)
            .filter(Prediccion.partido_id == partido_id)
            .all()
        )

    # Historial completo, más reciente primero — para la pantalla "Mis
    # predicciones". estado filtra por: "pendiente" (acerto IS NULL),
    # "acertada"/"fallada" (acerto True/False). Sin usuario_id en la
    # tabla todavía (ver HANDOFF) — esto es TODO lo guardado, no
    # filtrado por cuenta; en un solo-usuario real hoy no importa.
    def listar(self, estado: str | None = None, limite: int = 100,
               usuario_id: int | None = None) -> List[Prediccion]:
        """usuario_id es OBLIGATORIO en la práctica para la pantalla de
        "Mis predicciones": sin filtrar, un usuario veía las de todos.
        Se deja opcional para los usos internos (MLOps) que sí necesitan
        mirar todas."""
        q = self.db.query(Prediccion)
        if usuario_id is not None:
            q = q.filter(Prediccion.usuario_id == usuario_id)
        if estado == "pendiente":
            q = q.filter(Prediccion.acerto.is_(None))
        elif estado == "acertada":
            q = q.filter(Prediccion.acerto.is_(True))
        elif estado == "fallada":
            q = q.filter(Prediccion.acerto.is_(False))
        return q.order_by(Prediccion.creado_en.desc()).limit(limite).all()

    #Obtener las estadisticas — global y por mercado. Global mezcla
    # distintas fuentes de predicción (XGBoost solo vs ensemble de 4
    # modelos) si ambas están corriendo — por mercado es lo que importa
    # para saber si el ensemble realmente mejora sobre el modelo base.
    def get_stats(self) -> Dict:
        def _calcular(query):
            total = query.count()
            acertadas = query.filter(Prediccion.acerto == True).count()
            falladas = query.filter(Prediccion.acerto == False).count()
            pendientes = query.filter(Prediccion.acerto == None).count()
            accuracy = round(acertadas / (acertadas + falladas), 4) \
                if (acertadas + falladas) > 0 else None
            return {
                "total": total, "acertadas": acertadas, "falladas": falladas,
                "pendientes": pendientes, "accuracy": accuracy,
            }

        global_ = _calcular(self.db.query(Prediccion))

        mercados = [m[0] for m in self.db.query(Prediccion.mercado).distinct().all()]
        por_mercado = {
            m: _calcular(self.db.query(Prediccion).filter(Prediccion.mercado == m))
            for m in mercados
        }

        parlays_q = self.db.query(Parlay)
        parlays_total = parlays_q.count()
        parlays_ok = parlays_q.filter(Parlay.acerto == True).count()
        parlays_mal = parlays_q.filter(Parlay.acerto == False).count()
        parlays_pend = parlays_q.filter(Parlay.acerto == None).count()
        parlays_accuracy = round(parlays_ok / (parlays_ok + parlays_mal), 4) \
            if (parlays_ok + parlays_mal) > 0 else None

        return {
            **global_,
            "por_mercado": por_mercado,
            "parlays": {
                "total": parlays_total, "acertados": parlays_ok,
                "fallados": parlays_mal, "pendientes": parlays_pend,
                "accuracy": parlays_accuracy,
            },
        }

    def marcar_resultado (self, partido_id: int,
                          resultado_real: str) -> None:
        """Cierra TODAS las predicciones de un partido con el mismo
        resultado_real — solo válido si todas son mercado 1X2 (compara
        por igualdad directa de label). Para partidos con mercados
        mixtos (goles O/U, BTTS, etc junto con 1X2) usar cerrar_prediccion()
        fila por fila, ver job_cerrar_predicciones.py."""
        predicciones = self.get_por_partido(partido_id)
        for pred in predicciones:
            pred.resultado_real = resultado_real
            pred.acerto = (pred.prediccion == resultado_real)
        self.db.commit()

    def cerrar_prediccion(self, prediccion_id: int, acerto: bool,
                          resultado_real_texto: str) -> None:
        """Cierra UNA predicción puntual, ya resuelta externamente (ver
        resolver_mercado.py) — a diferencia de marcar_resultado(), no
        asume que todas las filas de un partido comparten el mismo
        formato de resultado."""
        pred = self.db.get(Prediccion, prediccion_id)
        if pred is None:
            return
        pred.acerto = acerto
        pred.resultado_real = resultado_real_texto
        self.db.commit()


