import logging
from uuid import uuid4

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.db.database import crear_tablas
from backend.core.config import get_settings
from backend.core.deps import get_usuario_actual
from backend.api.routes import partidos, predicciones, stats, auth
from backend.core.rate_limit import limiter

settings = get_settings()
log = logging.getLogger(__name__)
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Motor de pronosticos deportivos con ML"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://novitec.com.ec",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    if not settings.debug and settings.jwt_secret_key == "dev-secret-cambiar-en-produccion":
        raise RuntimeError("JWT_SECRET_KEY insegura: configurá una clave de producción")
    crear_tablas()


@app.exception_handler(Exception)
async def error_no_controlado(request: Request, exc: Exception):
    correlacion = uuid4().hex
    log.exception("Error no controlado [%s] %s %s", correlacion, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno", "correlation_id": correlacion},
    )


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
