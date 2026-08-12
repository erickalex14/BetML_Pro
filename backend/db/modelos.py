from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float,
    DateTime, Date, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship, backref
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

    id            = Column(Integer, primary_key=True)
    nombre        = Column(String(100), nullable=False)
    pais          = Column(String(50))
    logo_url      = Column(String(255))
    sofascore_id  = Column(Integer, nullable=True, unique=True)
    creado_en     = Column(DateTime, default=datetime.utcnow)

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
    minuto          = Column(Integer, nullable=True)  # elapsed de API-Football, solo mientras está en vivo
    goles_local     = Column(Integer, nullable=True)
    goles_visitante = Column(Integer, nullable=True)
    goles_local_ht  = Column(Integer, nullable=True)
    goles_visit_ht  = Column(Integer, nullable=True)
    temporada       = Column(Integer, nullable=False)
    jornada         = Column(String(50))
    sofascore_id    = Column(BigInteger, nullable=True, unique=True)
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


class EstadisticaSofascore(Base):
    """
    Stats avanzadas del partido desde Sofascore.
    xG, presiones, duelos, pases progresivos —
    """
    __tablename__ = "estadisticas_sofascores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), unique=True)

    #Expected goals
    xg_local = Column(Float, nullable=True)
    xg_visitante = Column(Float, nullable=True)

    #Tiros
    tiros_local = Column(Integer, nullable=True)
    tiros_visitante = Column(Integer, nullable=True)
    tiros_arco_local = Column(Integer, nullable=True)
    tiros_arco_visitante = Column(Integer, nullable=True)
    tiros_bloq_local = Column(Integer, nullable=True)
    tiros_bloq_visitante = Column(Integer, nullable=True)

    #posesion
    posesion_local = Column(Float, nullable=True)
    posesion_visitante = Column(Float, nullable=True)

    #pases
    pases_local = Column(Integer, nullable=True)
    pases_visitante = Column(Integer, nullable=True)
    precision_pases_local = Column(Float, nullable=True)
    precision_pases_visitante = Column(Float, nullable=True)
    pases_clave_local = Column(Integer, nullable=True)
    pases_clave_visitante = Column(Integer, nullable=True)

    #Corners y faltas
    corners_local = Column(Integer, nullable=True)
    corners_visitante = Column(Integer, nullable=True)
    faltas_local = Column(Integer, nullable=True)
    faltas_visitante = Column(Integer, nullable=True)

    #presiones
    presiones_local = Column(Integer, nullable=True)
    presiones_visitante = Column(Integer, nullable=True)

    #Duelos
    duelos_local = Column(Integer, nullable=True)
    duelos_visitante = Column(Integer, nullable=True)
    duelos_aereos_local = Column(Integer, nullable=True)
    duelos_aereos_visitante = Column(Integer, nullable=True)

    #Tarjetas
    amarillas_local = Column(Integer, nullable=True)
    amarillas_visitante = Column(Integer, nullable=True)
    rojas_local = Column(Integer, nullable=True)
    rojas_visitante = Column(Integer, nullable=True)

    #offsides
    fuera_juego_local = Column(Integer, nullable=True)
    fuera_juego_visitante = Column(Integer, nullable=True)

    #ID interno para refs cruzadas
    sofascore_id = Column(Integer, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    partido = relationship("Partido", backref=backref("stats_sofascore", uselist=False))

    def __repr__(self):
        return f"<EstadisticaSofascore {self.partido_id}>"


class EstadisticaJugador(Base):
    __tablename__ = "estadisticas_jugador"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    partido_id           = Column(Integer, ForeignKey("partidos.id"))
    equipo_id            = Column(Integer, ForeignKey("equipos.id"))
    sofascore_jugador_id = Column(Integer, nullable=False)
    nombre               = Column(String(100), nullable=False)
    posicion             = Column(String(20), nullable=True)
    es_local             = Column(Boolean, nullable=False)
    titular              = Column(Boolean, default=False)

    # Rating
    rating               = Column(Float, nullable=True)

    # Participación
    minutos_jugados      = Column(Integer, nullable=True)

    # Ataque
    goles                = Column(Integer, nullable=True)
    asistencias          = Column(Integer, nullable=True)
    xg_individual        = Column(Float, nullable=True)
    tiros                = Column(Integer, nullable=True)
    tiros_arco           = Column(Integer, nullable=True)
    atajadas             = Column(Integer, nullable=True)  # solo relevante para arqueros (posicion="G")

    # Creación
    pases_clave          = Column(Integer, nullable=True)
    grandes_ocasiones    = Column(Integer, nullable=True)
    regates_completados  = Column(Integer, nullable=True)

    # Pases
    pases_completados    = Column(Integer, nullable=True)
    precision_pases      = Column(Float, nullable=True)

    # Defensa
    duelos_ganados       = Column(Integer, nullable=True)
    duelos_aereos_gan    = Column(Integer, nullable=True)
    despejes             = Column(Integer, nullable=True)
    intercepciones       = Column(Integer, nullable=True)

    # Disciplina
    amarilla             = Column(Boolean, default=False)
    roja                 = Column(Boolean, default=False)

    creado_en            = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EstadisticaJugador {self.nombre} partido={self.partido_id}>"


class Parlay(Base):
    """Apuesta combinada guardada — ver /predicciones/combinada.
    acerto=None mientras algún partido de sus selecciones no haya
    terminado; una vez que todos terminen, acerto = AND de todas las
    patas (una sola que pierda tumba el combinado entero)."""
    __tablename__ = "parlays"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id       = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    cuota_combinada  = Column(Float, nullable=False)
    prob_combinada   = Column(Float, nullable=False)
    stake_pct        = Column(Float, nullable=True)
    bankroll         = Column(Float, nullable=True)
    acerto           = Column(Boolean, nullable=True)
    creado_en        = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Parlay {self.id} cuota={self.cuota_combinada} acerto={self.acerto}>"


class ParlaySeleccion(Base):
    """Una pata de un Parlay — mercado usa la misma convención de clave
    interna que resolver_mercado.py (odds_key sin el prefijo 'odds_')."""
    __tablename__ = "parlay_selecciones"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    parlay_id   = Column(Integer, ForeignKey("parlays.id"), nullable=False)
    partido_id  = Column(Integer, ForeignKey("partidos.id"), nullable=False)
    mercado     = Column(String(50), nullable=False)
    nombre      = Column(String(100), nullable=True)  # nombre legible, ej "Goles Over 2.5"
    probabilidad = Column(Float, nullable=False)
    cuota       = Column(Float, nullable=False)
    acerto      = Column(Boolean, nullable=True)

    def __repr__(self):
        return f"<ParlaySeleccion {self.mercado} partido={self.partido_id} acerto={self.acerto}>"


class Usuario(Base):
    __tablename__ = "usuarios"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    email          = Column(String(255), nullable=False, unique=True)
    password_hash  = Column(String(255), nullable=False)
    activo         = Column(Boolean, default=True)
    creado_en      = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Usuario {self.email}>"


class Odds(Base):
    """Cuotas reales de casas de apuestas — API-Football /odds (gratis
    por fixture_id, ver backend/pipeline/job_odds.py). mercado usa la
    MISMA convención de nombres que kelly.py (odds_local, odds_goles_over_2_5,
    etc) — se puede pasar directo a analizar_mercados_kelly() sin traducir."""
    __tablename__ = "odds"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    partido_id     = Column(Integer, ForeignKey("partidos.id"), nullable=False)
    bookmaker      = Column(String(50), nullable=False)
    mercado        = Column(String(50), nullable=False)
    valor          = Column(Float, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Odds {self.mercado}={self.valor} ({self.bookmaker}) partido={self.partido_id}>"


class LigaSofascoreTorneo(Base):
    """Ids de torneo de Sofascore aprendidos para una liga nuestra.

    Una liga nuestra puede corresponder a VARIOS torneos de Sofascore —
    "Conference League" son dos (fase principal y clasificación, ids
    distintos), y los amistosos están repartidos en varios torneos
    además de "Club Friendly Games". Por eso es una tabla y no una
    columna en Liga.

    Se llena solo, la primera vez que el descubridor encuentra el torneo
    de un partido que no se pudo anclar con LIGAS_SOFASCORE — ver
    backend/pipeline/sofascore/descubridor_torneos.py."""
    __tablename__ = "liga_sofascore_torneo"

    liga_id             = Column(Integer, ForeignKey("ligas.id"), primary_key=True)
    sofascore_torneo_id = Column(Integer, primary_key=True)
    nombre_sofascore    = Column(String(150))
    creado_en           = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LigaSofascoreTorneo liga={self.liga_id} torneo={self.sofascore_torneo_id} {self.nombre_sofascore!r}>"


class PresupuestoApiFootball(Base):
    """Contador de requests gastadas a API-Football por día — el plan free
    da 100/día, reset a medianoche UTC (ver backend/pipeline/presupuesto.py).
    Sin esto ningún job sabe cuánto queda del total compartido."""
    __tablename__ = "presupuesto_api_football"

    fecha  = Column(Date, primary_key=True)
    usados = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<PresupuestoApiFootball {self.fecha}: {self.usados}>"




