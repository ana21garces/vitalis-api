import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories import encuesta_hplp_repository as repo
from app.schemas.seguimiento_recomendacion import (
    ProgresoSeguimientoResponse,
    RegistrarDiaRequest,
    RegistrarDiaResponse,
    RegistroDiarioResponse,
    SeguimientoResponse,
    TarjetasSeguimientoResponse,
)
from app.services.seguimiento_recomendacion_service import SeguimientoRecomendacionService

router = APIRouter(prefix="/seguimiento-recomendaciones", tags=["Seguimiento de Recomendaciones"])

DimensionSlug = Literal[
    "actividad-fisica",
    "nutricion",
    "responsabilidad-salud",
    "manejo-estres",
    "relaciones-interpersonales",
    "psicologia-positiva",
]

SLUG_A_DIMENSION = {
    "actividad-fisica": "actividad_fisica",
    "nutricion": "nutricion",
    "responsabilidad-salud": "responsabilidad_salud",
    "manejo-estres": "manejo_estres",
    "relaciones-interpersonales": "relaciones_interpersonales",
    "psicologia-positiva": "psicologia_positiva",
}

SIN_ENCUESTA = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="El usuario aún no ha completado la encuesta",
)


@router.get("/{dimension}/tarjetas", response_model=TarjetasSeguimientoResponse)
def tarjetas_con_seguimiento(
    dimension: DimensionSlug,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise SIN_ENCUESTA

    return SeguimientoRecomendacionService(db).obtener_tarjetas_con_seguimiento(
        current_user, SLUG_A_DIMENSION[dimension], ultimo,
    )


@router.post("/{seguimiento_id}/registrar-dia", response_model=RegistrarDiaResponse)
def registrar_dia(
    seguimiento_id: uuid.UUID,
    body: RegistrarDiaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return SeguimientoRecomendacionService(db).registrar_dia(current_user, seguimiento_id, body.notas)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{seguimiento_id}/completar", response_model=SeguimientoResponse)
def completar(
    seguimiento_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return SeguimientoRecomendacionService(db).completar_manualmente(current_user, seguimiento_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{seguimiento_id}/historial", response_model=list[RegistroDiarioResponse])
def historial(
    seguimiento_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return SeguimientoRecomendacionService(db).historial(current_user, seguimiento_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/progreso", response_model=ProgresoSeguimientoResponse)
def progreso(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise SIN_ENCUESTA

    return SeguimientoRecomendacionService(db).progreso_general(current_user, ultimo)
