from sqlalchemy import create_engine, false
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.pipeline.config import DB_URL

# El "engine" es la conexión a la base de datos.
engine = create_engine(
    DB_URL,
    # echo=True imprime el SQL generado en consola.
    # Útil para aprender/debuggear, lo ponemos en False
    # cuando el proyecto esté en producción.
    echo=false,
    # Solo necesario para SQLite — permite usar la misma
    # conexión desde múltiples partes del código.
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
