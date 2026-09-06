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
from app.schemas.insignia import InsigniasResponse
from app.services.gamificacion_service import GamificacionService
from app.services.insignias_service import InsigniasService

router = APIRouter(prefix="/gamificacion", tags=["Gamificación"])

AVATAR_DIR = Path("uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}
AVATAR_MAX_BYTES = 2 * 1024 * 1024
_CHUNK = 64 * 1024


def _tipo_real(cabecera: bytes) -> str | None:
    """Detecta el formato por los bytes de cabecera, sin fiarse de lo que
    declara el cliente (el `content_type` se puede falsear)."""
    if cabecera.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if cabecera.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP":
        return "image/webp"
    return None


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


@router.get("/insignias", response_model=InsigniasResponse)
def insignias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Catálogo de insignias con cuáles ha ganado el usuario. Al consultarlas se
    evalúan y otorgan las que ya cumple (con su bonus de XP)."""
    return InsigniasService(db).obtener(current_user)


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

    # Se lee por trozos y se corta en cuanto pasa del límite: así un archivo
    # enorme no se llega a cargar entero en memoria.
    contenido = bytearray()
    while True:
        trozo = await archivo.read(_CHUNK)
        if not trozo:
            break
        contenido.extend(trozo)
        if len(contenido) > AVATAR_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La imagen no puede superar 2 MB.",
            )

    # El formato se decide por los bytes reales, no por el content_type.
    tipo = _tipo_real(bytes(contenido[:16]))
    if tipo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es una imagen JPG, PNG o WebP válida.",
        )

    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[tipo]
    destino = AVATAR_DIR / f"{current_user.id}{ext}"

    for viejo in AVATAR_DIR.glob(f"{current_user.id}.*"):
        viejo.unlink(missing_ok=True)

    destino.write_bytes(bytes(contenido))
    current_user.avatar_url = f"/uploads/avatars/{current_user.id}{ext}"
    db.commit()
    db.refresh(current_user)

    return GamificacionService(db).progreso(current_user)
