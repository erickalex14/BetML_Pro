from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import crear_tablas
from backend.core.config import get_settings
from backend.core.deps import get_usuario_actual
from backend.api.routes import partidos, predicciones, stats, auth

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
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


# Registra los routers — cada uno en su archivo.
# /auth queda abierto (necesitás poder loguearte sin estar logueado
# todavía). El resto requiere JWT válido — dependencies a nivel de router
# protege TODOS los endpoints de ese archivo sin tocar cada función.
app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(
    partidos.router, prefix="/partidos", tags=["Partidos"],
    dependencies=[Depends(get_usuario_actual)])
app.include_router(
    predicciones.router, prefix="/predicciones", tags=["Predicciones"],
    dependencies=[Depends(get_usuario_actual)])
app.include_router(
    stats.router, prefix="/stats", tags=["Stats"],
    dependencies=[Depends(get_usuario_actual)])