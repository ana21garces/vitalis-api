import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.repositories import notificacion_repository as repo
from app.repositories.user_repository import UserRepository
from app.schemas.notificacion import NotificacionCreate, NotificacionResponse

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])

# Roles que pueden invitar a un estudiante a agendar una cita desde su vista
# de resultados.
ROLES_QUE_NOTIFICAN = {
    UserRole.CAPELLAN,
    UserRole.ACTIVIDAD_FISICA,
    UserRole.RESPONSABILIDAD_SALUD,
    UserRole.RELACIONES_INTERPERSONALES,
    UserRole.MANEJO_ESTRES,
}


@router.post("", response_model=NotificacionResponse, status_code=status.HTTP_201_CREATED)
def enviar_notificacion(
    data: NotificacionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Un profesional invita a un estudiante a agendar una cita."""
    if current_user.role not in {r.value for r in ROLES_QUE_NOTIFICAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu rol no puede enviar notificaciones",
        )

    try:
        destinatario_uuid = uuid.UUID(data.destinatario_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="destinatario_id inválido")

    destinatario = UserRepository(db).get_by_id(destinatario_uuid)
    if destinatario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El destinatario no existe")
    if destinatario.role != UserRole.STUDENT.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Solo se puede notificar a estudiantes",
        )

    notificacion = repo.crear(db, current_user.id, destinatario_uuid, data.mensaje)
    return NotificacionResponse(
        id=notificacion.id,
        remitente_nombre=current_user.full_name,
        mensaje=notificacion.mensaje,
        leida=notificacion.leida,
        created_at=notificacion.created_at,
    )


@router.get("", response_model=list[NotificacionResponse])
def mis_notificaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Notificaciones recibidas por el usuario autenticado, más recientes primero."""
    notificaciones = repo.listar_por_destinatario(db, current_user.id)

    user_repo = UserRepository(db)
    nombres_por_remitente: dict[uuid.UUID, str] = {}

    def nombre_de(remitente_id: uuid.UUID) -> str:
        if remitente_id not in nombres_por_remitente:
            remitente = user_repo.get_by_id(remitente_id)
            nombres_por_remitente[remitente_id] = remitente.full_name if remitente else "Equipo Vitalis"
        return nombres_por_remitente[remitente_id]

    return [
        NotificacionResponse(
            id=n.id,
            remitente_nombre=nombre_de(n.remitente_id),
            mensaje=n.mensaje,
            leida=n.leida,
            created_at=n.created_at,
        )
        for n in notificaciones
    ]


@router.patch("/{notificacion_id}/leida", response_model=NotificacionResponse)
def marcar_como_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """El destinatario descarta la notificación una vez la vio."""
    notificacion = repo.marcar_leida(db, notificacion_id, current_user.id)
    if notificacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")

    remitente = UserRepository(db).get_by_id(notificacion.remitente_id)
    return NotificacionResponse(
        id=notificacion.id,
        remitente_nombre=remitente.full_name if remitente else "Equipo Vitalis",
        mensaje=notificacion.mensaje,
        leida=notificacion.leida,
        created_at=notificacion.created_at,
    )
