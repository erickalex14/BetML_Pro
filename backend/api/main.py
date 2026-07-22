from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import crear_tablas
from backend.core.config import get_settings
from backend.api.routes import partidos, predicciones, stats

settings = get_settings()
app = FastAPI(
    tittle=settings.app_name,
    version=settings.app_version,
    description="Motor de pronosticos deportivos con ML"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    crear_tablas()


@app.get("/")
def root():
    return {"app": settings.app_name, "version": settings.app_version}


@app.get("/health")
def health():
    return {"status": "ok"}


# Registra los routers — cada uno en su archivo
app.include_router(partidos.router,     prefix="/partidos",     tags=["Partidos"])
app.include_router(predicciones.router, prefix="/predicciones", tags=["Predicciones"])
app.include_router(stats.router,        prefix="/stats",        tags=["Stats"])