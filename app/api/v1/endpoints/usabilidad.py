from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, requiere_admin
from app.data.csuq import CSUQ_ITEMS, ESCALA_MAX, ESCALA_MIN
from app.models.user import User, UserRole
from app.schemas.usabilidad import (
    CampanaResponse,
    CampanaUpdate,
    UsabilidadCreate,
    UsabilidadEstado,
    UsabilidadResultado,
)
from app.services import usabilidad_service as svc

router = APIRouter(prefix="/usabilidad", tags=["Usabilidad"])


@router.get("/preguntas")
def preguntas() -> dict:
    return {"items": CSUQ_ITEMS, "escala_min": ESCALA_MIN, "escala_max": ESCALA_MAX}


@router.get("/estado", response_model=UsabilidadEstado)
def estado(
    rol: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UsabilidadEstado:
    efectivo = svc.rol_efectivo(current_user, rol)
    respondida = svc.ya_respondio(db, current_user.id, efectivo)
    abierta = svc.campana_abierta(db)
    # El admin nunca queda bloqueado (para poder cerrar la campaña); los demás
    # roles quedan obligados mientras la campaña esté abierta y no respondan.
    requerida = abierta and not respondida and current_user.role != UserRole.ADMIN.value
    return UsabilidadEstado(respondida=respondida, requerida=requerida, abierta=abierta)


@router.post("", response_model=UsabilidadResultado, status_code=status.HTTP_201_CREATED)
def responder(
    payload: UsabilidadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UsabilidadResultado:
    efectivo = svc.rol_efectivo(current_user, payload.rol)
    if svc.ya_respondio(db, current_user.id, efectivo):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya respondiste la encuesta de usabilidad",
        )
    fila = svc.guardar(db, current_user, payload.respuestas, efectivo)
    return UsabilidadResultado(
        sysuse=fila.sysuse,
        infoqual=fila.infoqual,
        interqual=fila.interqual,
        puntaje_global=fila.puntaje_global,
    )


def _campana_response(db: Session) -> CampanaResponse:
    campana = svc.obtener_campana(db)
    return CampanaResponse(
        activa=campana.activa,
        fecha_inicio=campana.fecha_inicio,
        fecha_fin=campana.fecha_fin,
        abierta=svc.campana_abierta(db),
        total_respuestas=svc.total_respuestas(db),
    )


@router.get("/campana", response_model=CampanaResponse)
def obtener_campana(
    db: Session = Depends(get_db),
    _admin: User = Depends(requiere_admin),
) -> CampanaResponse:
    return _campana_response(db)


@router.put("/campana", response_model=CampanaResponse)
def actualizar_campana(
    payload: CampanaUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(requiere_admin),
) -> CampanaResponse:
    svc.guardar_campana(db, payload.activa, payload.fecha_inicio, payload.fecha_fin)
    return _campana_response(db)
