from sqlalchemy import create_engine, false
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path
from backend.pipeline.config import DB_URL, ROOT_DIR

DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "betml.db"
DB_URL_ABSOLUTA = f"sqlite:///{DB_PATH}"

# El "engine" es la conexión a la base de datos.
engine = create_engine(
    DB_URL_ABSOLUTA,
    connect_args={"check_same_thread": False}
)

# La SessionLocal es la fábrica de sesiones.
# Cada vez que necesites hablar con la BD, creas una

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base es la clase padre de todos los modelos/tablas.
class Base(DeclarativeBase):
    pass

"""
    Función generadora que abre una sesión, la entrega,
    y la cierra automáticamente cuando termina — aunque
    haya un error. Equivalente al try-with-resources de Java.
"""
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
    Crea todas las tablas en la BD si no existen.
    Equivalente al hibernate.ddl-auto=create en Spring.
    Solo crea — nunca borra datos existentes.
"""
def crear_tablas():
    Base.metadata.create_all(bind=engine)
