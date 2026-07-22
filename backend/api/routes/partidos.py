from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from backend.db.database import get_db
from backend.services.partido_service import PartidoService
from backend.services.prediccion_service import PrediccionService

router = APIRouter()

#Ruta para obtener los partidos del dia
@router.get("/hoy")
def partidos_hoy(db: Session = Depends(get_db)):
    service = PartidoService(db)
    return service.get_partidos_hoy()


@router.get("/{partido_id}")
def detalle_partido(partido_id: int, db: Session = Depends(get_db)):
    from backend.repositories.partido_repo import PartidoRepository
    repo = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return partido


@router.get("/{partido_id}/prediccion")
def prediccion_partido(partido_id: int, db: Session = Depends(get_db)):
    from backend.repositories.partido_repo import PartidoRepository
    repo = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    service = PrediccionService(db)
    pred = service.predecir(partido)
    if not pred:
        raise HTTPException(status_code=422, detail="Sin historial reciente")
    return pred


@router.get("/liga/{liga_id}")
def partidos_liga(liga_id: int, db: Session = Depends(get_db)):
    service = PartidoService(db)
    return service.get_por_liga(liga_id)