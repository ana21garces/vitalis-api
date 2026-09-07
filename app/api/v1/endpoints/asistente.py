from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.asistente import AsistenteMensajeResponse
from app.services import asistente_service

router = APIRouter(prefix="/asistente", tags=["Asistente"])


@router.get("/mensaje", response_model=AsistenteMensajeResponse)
def mensaje_asistente(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AsistenteMensajeResponse:
    if current_user.role != UserRole.STUDENT.value:
        return AsistenteMensajeResponse(
            mensaje="", misiones=[], plan=[], pendientes=0, todo_hecho=True
        )
    datos = asistente_service.generar_mensaje(db, current_user)
    return AsistenteMensajeResponse(**datos)
