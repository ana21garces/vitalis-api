import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.gamificacion import (
    CompletarMisionResponse,
    MisionesHoyResponse,
    ProgresoGamificacion,
    XpEventoResponse,
)
from app.services.gamificacion_service import GamificacionService

router = APIRouter(prefix="/gamificacion", tags=["Gamificación"])

AVATAR_DIR = Path("uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.get("/misiones/hoy", response_model=MisionesHoyResponse)
def misiones_hoy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return GamificacionService(db).obtener_misiones_hoy(current_user)


@router.post("/misiones/{mision_id}/completar", response_model=CompletarMisionResponse)
def completar_mision(
    mision_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = GamificacionService(db)
    try:
        return service.completar_mision(current_user, mision_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/progreso", response_model=ProgresoGamificacion)
def progreso(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return GamificacionService(db).progreso(current_user)


@router.get("/historial", response_model=list[XpEventoResponse])
def historial(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return GamificacionService(db).historial(current_user)


@router.post("/avatar", response_model=ProgresoGamificacion)
async def subir_avatar(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if archivo.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Usa JPG, PNG o WebP.",
        )

    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }[archivo.content_type]

    destino = AVATAR_DIR / f"{current_user.id}{ext}"
    contenido = await archivo.read()
    if len(contenido) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen no puede superar 2 MB.",
        )

    for viejo in AVATAR_DIR.glob(f"{current_user.id}.*"):
        viejo.unlink(missing_ok=True)

    destino.write_bytes(contenido)
    current_user.avatar_url = f"/uploads/avatars/{current_user.id}{ext}"
    db.commit()
    db.refresh(current_user)

    return GamificacionService(db).progreso(current_user)
