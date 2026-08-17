from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.db.modelos import Partido, EstadisticaPartido
from backend.pipeline.config import rango_utc_dia_partidos

class PartidoRepository:

    def __init__(self, db: Session):
        self.db = db

    #Obetener partido por ID
    def get_por_id(self, partdo_id: int) -> Optional[Partido]:
        return self.db.get(Partido, partdo_id)

    #Obtener partido por fecha
    def get_por_fecha(self, fecha: date) -> List[Partido]:
        inicio_utc, fin_utc = rango_utc_dia_partidos(fecha)
        return (
            self.db.query(Partido)
            .options(
                joinedload(Partido.equipo_local),
                joinedload(Partido.equipo_visitante),
                joinedload(Partido.liga),
                joinedload(Partido.estadisticas),
                joinedload(Partido.stats_sofascore),
            )
            .filter(
                Partido.fecha >= inicio_utc,
                Partido.fecha < fin_utc,
            )
            .order_by(Partido.fecha.asc())
            .all()
        )

    #Obtener los partidos por liga
    def get_por_liga(self, liga_id: int, limite: int = 10) -> List[Partido]:
        return(
            self.db.query(Partido)
            .filter(
                Partido.liga_id == liga_id,
                Partido.estado == "FT",
            )
            .order_by(Partido.fecha.desc())
            .limit(limite)
            .all()
        )

    #Obtener partidos por temporada
    def get_por_temporada(self, temporadas: List[int],
                          estado: str = "FT") -> List[Partido]:
        return(
            self.db.query(Partido)
            .filter(
                Partido.temporada.in_(temporadas),
                Partido.estado == estado,
                Partido.goles_local != None
            )
            .order_by(Partido.fecha.asc())
            .all()
        )

    #Obtener el historial de local de un equipo
    def get_historial_local(self, equipo_id: int,
                            fecha_limite, n: int = 10) -> List[Partido]:
        return(
            self.db.query(Partido)
            .filter(
                Partido.equipo_local_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_local != None
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
            .all()
        )

    #Obtiene el hitorial de visitante de un equipo
    def get_historial_visitante(self, equipo_id: int,
                                fecha_limite, n: int = 10) -> List[Partido]:
        return (
            self.db.query(Partido)
            .filter(
                Partido.equipo_visit_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_visitante != None
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
            .all()
        )

    #Obtiene el H2H DE UN PARTIDO
    def get_h2h(self, local_id: int, visit_id: int,
            fecha_limite, n: int = 5) -> List[Partido]:
        return (
            self.db.query(Partido)
            .filter(
                Partido.equipo_local_id == local_id,
                Partido.equipo_visit_id == visit_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_local != None
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
            .all()
        )

    #Obtiene estadisticas pedientes
    def get_pendietes_stats(self,
                            temporadas:List[int])-> List[Partido]:
        return (
            self.db.query(Partido)
            .outerjoin(EstadisticaPartido)
            .filter(
                Partido.estado == "FT",
                Partido.temporada.in_(temporadas),
                EstadisticaPartido.id == None
            )
            .order_by(Partido.fecha.desc())
            .all()
        )

    #Guardar partido en la BD
    def guardar(self, partido: Partido) -> Partido:
        self.db.add(partido)
        self.db.commit()
        self.db.refresh(partido)
        return partido


    #Actualizar un partido
    def acttualizar(self) -> None:
        self.db.commit()


