from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from backend.db.database import Base

"""
Tabla de ligas y competiciones.
Se llena una vez y se actualiza poco — es datos de referencia.
"""
class Liga(Base):
    __tablename__ = 'ligas'
    id          = Column(Integer, primary_key=True)  # ID de API-Football
    nombre      = Column(String(100), nullable=False)
    pais        = Column(String(50))
    temporada   = Column(Integer)
    activa      = Column(Boolean, default=True)
    creado_en   = Column(DateTime, default=datetime.utcnow)
    # Un liga tiene muchos partidos — relación 1:N
    partidos = relationship("Partido", back_populates="ligas")
    def __repr__(self):
        return f"<Liga {self.nombre} {self.temporada}>"

"""
    Tabla de equipos.
"""
class Equipo(Base):
    __tablename__ = 'equipos'
    id = Column(Integer, primary_key=True)  # ID de API-Football
    nombre = Column(String(100), nullable=False)
    pais = Column(String(50))
    logo_url = Column(String(255))
    creado_en = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Equipo {self.nombre}>"

"""
    Tabla principal — un registro por partido.
    Es la tabla más importante del proyecto:
    de aquí salen los datos para entrenar el modelo ML.
"""
class Partido(Base):
    __tablename__ = 'partidos'
    id              = Column(Integer, primary_key=True)  # ID de API-Football
    liga_id         = Column(Integer, ForeignKey("ligas.id"), nullable=False)
    equipo_local_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    equipo_visit_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)

    # Fecha y hora del partido en UTC
    fecha           = Column(DateTime, nullable=False)

    # Estado: NS=Not Started, 1H=Primera parte,
    #         HT=Descanso, 2H=Segunda parte, FT=Terminado
    estado          = Column(String(10), default="NS")

    # Resultados — None si el partido no ha terminado
    goles_local     = Column(Integer, nullable=True)
    goles_visitante = Column(Integer, nullable=True)
    goles_local_ht  = Column(Integer, nullable=True)  # al descanso
    goles_visit_ht  = Column(Integer, nullable=True)

    # Metadatos
    temporada       = Column(Integer, nullable=False)
    jornada         = Column(String(50))               # "Regular Season - 28"
    creado_en       = Column(DateTime, default=datetime.utcnow)
    actualizado_en  = Column(DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    # Relaciones
    liga            = relationship("Liga", back_populates="partidos")
    equipo_local    = relationship("Equipo", foreign_keys=[equipo_local_id])
    equipo_visitante= relationship("Equipo", foreign_keys=[equipo_visit_id])
    estadisticas    = relationship("EstadisticaPartido",
                                   back_populates="partido",
                                   uselist=False)

    def __repr__(self):
        return f"<Partido {self.equipo_local_id} vs {self.equipo_visit_id} — {self.fecha}>"

"""
    Estadísticas detalladas de cada partido terminado.
    Estas son las FEATURES del modelo ML:
    tiros, corners, tarjetas, posesión, xG, etc.
    Se llena después de que termina el partido.
"""
class EstadisticaPartido(Base):
    __tablename__ = "estadisticas_partido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), unique=True)

    # Tiros
    tiros_local = Column(Integer, nullable=True)
    tiros_visit = Column(Integer, nullable=True)
    tiros_arco_local = Column(Integer, nullable=True)
    tiros_arco_visit = Column(Integer, nullable=True)

    # Posesión (porcentaje)
    posesion_local = Column(Float, nullable=True)
    posesion_visit = Column(Float, nullable=True)

    # Corners
    corners_local = Column(Integer, nullable=True)
    corners_visit = Column(Integer, nullable=True)

    # Tarjetas
    amarillas_local = Column(Integer, nullable=True)
    amarillas_visit = Column(Integer, nullable=True)
    rojas_local = Column(Integer, nullable=True)
    rojas_visit = Column(Integer, nullable=True)

    # Pases
    pases_local = Column(Integer, nullable=True)
    pases_visit = Column(Integer, nullable=True)
    precision_pases_local = Column(Float, nullable=True)
    precision_pases_visit = Column(Float, nullable=True)

    creado_en = Column(DateTime, default=datetime.utcnow)

    partido = relationship("Partido",
                           back_populates="estadisticas")

    def __repr__(self):
        return f"<Stats partido {self.partido_id}>"

"""
    Tabla de predicciones del modelo ML.
    Cada vez que el modelo predice un partido,
    guardamos la predicción aquí para después
    compararla con el resultado real (tracking MLOps).
"""
class Prediccion(Base):
    __tablename__ = "predicciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"))
    mercado = Column(String(50))  # "1X2", "BTTS", "Over2.5"
    prediccion = Column(String(50))  # "Local", "Si", "Over"
    probabilidad = Column(Float)  # 0.72
    confianza = Column(Float)  # 0.68
    resultado_real = Column(String(50), nullable=True)  # se llena al terminar
    acerto = Column(Boolean, nullable=True)  # True/False/None
    creado_en = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Prediccion {self.mercado} — {self.prediccion} ({self.probabilidad})>"