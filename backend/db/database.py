from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path
from backend.pipeline.config import DB_URL

engine =  create_engine(
    DB_URL,
    pool_size=8,
    max_overflow=4,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,     # ← correcto
    bind=engine
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def crear_tablas():
    from backend.db import modelos
    Base.metadata.create_all(bind=engine)




