import logging
from datetime import date
from sqlalchemy.orm import Session
from backend.db.modelos import Equipo, Liga
from backend.repositories.partido_repo import PartidoRepository

log = logging.getLogger(__name__)


class PartidoService:
    """
    Lógica de negocio relacionada a partidos.
    Ensambla los datos de múltiples repositorios
    en la respuesta final que consume la API.
    """

    def __init__(self, db: Session):
        self.db           = db
        self.partido_repo = PartidoRepository(db)

    def _enriquecer(self, partido, con_prediccion: bool = False) -> dict:
        """Convierte un objeto Partido en dict con datos relacionados.

        con_prediccion=True agrega la clave "prediccion" (None si falta
        historial suficiente) — usa PrediccionService.predecir(), el
        mismo predictor que /kelly, /montecarlo, etc. Import local para
        evitar import circular (prediccion_service no importa este
        módulo, pero mantiene el mismo patrón que el resto de las rutas)."""
        local     = self.db.get(Equipo, partido.equipo_local_id)
        visitante = self.db.get(Equipo, partido.equipo_visit_id)
        liga      = self.db.get(Liga, partido.liga_id)

        data = {
            "id":          partido.id,
            "liga":        liga.nombre if liga else "Desconocida",
            "liga_id":     partido.liga_id,
            "local":       local.nombre if local else "Desconocido",
            "local_id":    partido.equipo_local_id,
            "local_logo":  local.logo_url if local else None,
            "visitante":   visitante.nombre if visitante else "Desconocido",
            "visitante_id":partido.equipo_visit_id,
            "visitante_logo": visitante.logo_url if visitante else None,
            "fecha":       str(partido.fecha),
            "hora":        str(partido.fecha)[11:16],
            "estado":      partido.estado,
            "goles_local": partido.goles_local,
            "goles_visit": partido.goles_visitante,
            "temporada":   partido.temporada,
            "jornada":     partido.jornada,
        }

        if partido.estadisticas:
            e = partido.estadisticas
            data["estadisticas"] = {
                "tiros_local":      e.tiros_local,
                "tiros_visit":      e.tiros_visit,
                "tiros_arco_local": e.tiros_arco_local,
                "tiros_arco_visit": e.tiros_arco_visit,
                "posesion_local":   e.posesion_local,
                "posesion_visit":   e.posesion_visit,
                "corners_local":    e.corners_local,
                "corners_visit":    e.corners_visit,
                "amarillas_local":  e.amarillas_local,
                "amarillas_visit":  e.amarillas_visit,
                "rojas_local":      e.rojas_local,
                "rojas_visit":      e.rojas_visit,
            }

        if con_prediccion:
            from backend.services.prediccion_service import PrediccionService
            data["prediccion"] = PrediccionService(self.db).predecir(partido)

        return data

    def get_partidos_hoy(self) -> dict:
        partidos  = self.partido_repo.get_por_fecha(date.today())
        resultado = [self._enriquecer(p, con_prediccion=True) for p in partidos]
        return {
            "fecha":    str(date.today()),
            "partidos": resultado,
            "total":    len(resultado)
        }

    def get_detalle(self, partido_id: int) -> dict | None:
        partido = self.partido_repo.get_por_id(partido_id)
        if not partido:
            return None
        return self._enriquecer(partido, con_prediccion=True)

    def get_por_liga(self, liga_id: int) -> list[dict]:
        partidos = self.partido_repo.get_por_liga(liga_id)
        return [self._enriquecer(p) for p in partidos]