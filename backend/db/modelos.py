from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from backend.db.database import Base


class Liga(Base):
    __tablename__ = "ligas"

    id          = Column(Integer, primary_key=True)
    nombre      = Column(String(100), nullable=False)
    pais        = Column(String(50))
    temporada   = Column(Integer)
    activa      = Column(Boolean, default=True)
    creado_en   = Column(DateTime, default=datetime.utcnow)

    # El atributo se llama "partidos" — Partido apunta aquí
    partidos    = relationship("Partido", back_populates="liga")

    def __repr__(self):
        return f"<Liga {self.nombre} {self.temporada}>"


class Equipo(Base):
    __tablename__ = "equipos"

    id          = Column(Integer, primary_key=True)
    nombre      = Column(String(100), nullable=False)
    pais        = Column(String(50))
    logo_url    = Column(String(255))
    creado_en   = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Equipo {self.nombre}>"


class Partido(Base):
    __tablename__ = "partidos"

    id              = Column(Integer, primary_key=True)
    liga_id         = Column(Integer, ForeignKey("ligas.id"), nullable=False)
    equipo_local_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    equipo_visit_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    fecha           = Column(DateTime, nullable=False)
    estado          = Column(String(10), default="NS")
    goles_local     = Column(Integer, nullable=True)
    goles_visitante = Column(Integer, nullable=True)
    goles_local_ht  = Column(Integer, nullable=True)
    goles_visit_ht  = Column(Integer, nullable=True)
    temporada       = Column(Integer, nullable=False)
    jornada         = Column(String(50))
    creado_en       = Column(DateTime, default=datetime.utcnow)
    actualizado_en  = Column(DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    # back_populates="liga" apunta al atributo "liga" de esta
    # misma clase — NO al nombre de la tabla
    liga             = relationship("Liga", back_populates="partidos")
    equipo_local     = relationship("Equipo", foreign_keys=[equipo_local_id])
    equipo_visitante = relationship("Equipo", foreign_keys=[equipo_visit_id])
    estadisticas     = relationship(
                           "EstadisticaPartido",
                           back_populates="partido",
                           uselist=False
                       )

    def __repr__(self):
        return f"<Partido {self.equipo_local_id} vs {self.equipo_visit_id}>"


class EstadisticaPartido(Base):
    __tablename__ = "estadisticas_partido"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    partido_id            = Column(Integer, ForeignKey("partidos.id"), unique=True)
    tiros_local           = Column(Integer, nullable=True)
    tiros_visit           = Column(Integer, nullable=True)
    tiros_arco_local      = Column(Integer, nullable=True)
    tiros_arco_visit      = Column(Integer, nullable=True)
    posesion_local        = Column(Float, nullable=True)
    posesion_visit        = Column(Float, nullable=True)
    corners_local         = Column(Integer, nullable=True)
    corners_visit         = Column(Integer, nullable=True)
    amarillas_local       = Column(Integer, nullable=True)
    amarillas_visit       = Column(Integer, nullable=True)
    rojas_local           = Column(Integer, nullable=True)
    rojas_visit           = Column(Integer, nullable=True)
    pases_local           = Column(Integer, nullable=True)
    pases_visit           = Column(Integer, nullable=True)
    precision_pases_local = Column(Float, nullable=True)
    precision_pases_visit = Column(Float, nullable=True)
    creado_en             = Column(DateTime, default=datetime.utcnow)

    partido = relationship("Partido", back_populates="estadisticas")

    def __repr__(self):
        return f"<Stats partido {self.partido_id}>"


class Prediccion(Base):
    __tablename__ = "predicciones"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    partido_id     = Column(Integer, ForeignKey("partidos.id"))
    mercado        = Column(String(50))
    prediccion     = Column(String(50))
    probabilidad   = Column(Float)
    confianza      = Column(Float)
    resultado_real = Column(String(50), nullable=True)
    acerto         = Column(Boolean, nullable=True)
    creado_en      = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Prediccion {self.mercado} — {self.prediccion}>"