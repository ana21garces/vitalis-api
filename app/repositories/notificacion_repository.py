import uuid
from datetime import datetime, timezone

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion
from app.models.user import User, UserRole


def crear(
    db: Session,
    remitente_id: uuid.UUID,
    destinatario_id: uuid.UUID | None,
    mensaje: str,
    enlace: str | None = None,
    rol_destinatario: str | None = None,
    remitente_rol: str | None = None,
    tipo: str | None = None,
) -> Notificacion:
    notificacion = Notificacion(
        remitente_id=remitente_id,
        destinatario_id=destinatario_id,
        mensaje=mensaje,
        enlace=enlace,
        rol_destinatario=rol_destinatario,
        remitente_rol=remitente_rol,
        tipo=tipo,
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def crear_difusion(
    db: Session,
    remitente_id: uuid.UUID,
    destinatarios: list[uuid.UUID],
    mensaje: str,
) -> int:
    """Crea una notificación por destinatario, todas con el mismo instante.

    Compartir `created_at` es lo que permite agrupar después el envío como un
    solo anuncio en el historial, sin añadir una columna de lote.
    """
    ahora = datetime.now(timezone.utc)
    objetos = [
        Notificacion(remitente_id=remitente_id, destinatario_id=d, mensaje=mensaje, created_at=ahora)
        for d in destinatarios
    ]
    db.add_all(objetos)
    db.commit()
    return len(objetos)


def listar_enviadas(db: Session, limite: int = 100) -> list:
    """Historial agrupado: cada mensaje enviado en el mismo instante por el
    mismo remitente cuenta como un envío, con su total y cuántas se leyeron.

    Solo los mensajes dirigidos a personas (anuncios, invitaciones); las alertas
    por rol no son "envíos" de nadie, así que quedan fuera."""
    return (
        db.query(
            Notificacion.remitente_id,
            Notificacion.mensaje,
            Notificacion.created_at,
            func.count().label("total"),
            func.sum(case((Notificacion.leida.is_(True), 1), else_=0)).label("leidas"),
        )
        .filter(Notificacion.rol_destinatario.is_(None))
        .group_by(Notificacion.remitente_id, Notificacion.mensaje, Notificacion.created_at)
        .order_by(Notificacion.created_at.desc())
        .limit(limite)
        .all()
    )


def _roles_visibles(usuario: User, rol: str | None) -> set[str]:
    """Roles cuyas alertas puede ver este usuario en la campana: siempre el
    suyo, y el que pide ver si es administrador (entra a la vista de un
    profesional) o es justo su propio rol."""
    roles = {usuario.role}
    if rol and (usuario.role == UserRole.ADMIN.value or usuario.role == rol):
        roles.add(rol)
    return roles


def listar_para(db: Session, usuario: User, rol: str | None = None) -> list[Notificacion]:
    """Notificaciones de la campana de un usuario: las dirigidas a él y las
    alertas dirigidas a los roles que puede ver."""
    return (
        db.query(Notificacion)
        .filter(
            or_(
                Notificacion.destinatario_id == usuario.id,
                Notificacion.rol_destinatario.in_(_roles_visibles(usuario, rol)),
            )
        )
        .order_by(Notificacion.created_at.desc())
        .all()
    )


def obtener(db: Session, notificacion_id: int) -> Notificacion | None:
    return db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()


def estados_invitacion_por_rol(db: Session, rol: str) -> dict[str, str]:
    """Estado de la ÚLTIMA invitación a cita que envió ese rol a cada estudiante:
    `pendiente`, `aceptada` o `rechazada`.

    Se toma la última y no todas porque a una persona se la puede volver a
    invitar después de que rechace: lo que importa en la vista es en qué quedó
    el último intento.
    """
    filas = (
        db.query(Notificacion.destinatario_id, Notificacion.respuesta)
        .filter(Notificacion.remitente_rol == rol, Notificacion.destinatario_id.isnot(None))
        .order_by(Notificacion.created_at.asc(), Notificacion.id.asc())
        .all()
    )
    return {str(destinatario): respuesta or "pendiente" for destinatario, respuesta in filas}


def marcar_leida(db: Session, notificacion_id: int, usuario: User) -> Notificacion | None:
    """La marca como leída si va dirigida al usuario, o a un rol que él puede
    ver (su propio rol, o cualquiera si es administrador)."""
    notificacion = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
    if notificacion is None:
        return None

    es_suya = notificacion.destinatario_id == usuario.id
    es_de_su_rol = notificacion.rol_destinatario is not None and (
        usuario.role == UserRole.ADMIN.value or usuario.role == notificacion.rol_destinatario
    )
    if not (es_suya or es_de_su_rol):
        return None

    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)
    return notificacion
