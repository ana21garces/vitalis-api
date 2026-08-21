import uuid
from datetime import datetime, timezone

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion


def crear(db: Session, remitente_id: uuid.UUID, destinatario_id: uuid.UUID, mensaje: str) -> Notificacion:
    notificacion = Notificacion(
        remitente_id=remitente_id,
        destinatario_id=destinatario_id,
        mensaje=mensaje,
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
    mismo remitente cuenta como un envío, con su total y cuántas se leyeron."""
    return (
        db.query(
            Notificacion.remitente_id,
            Notificacion.mensaje,
            Notificacion.created_at,
            func.count().label("total"),
            func.sum(case((Notificacion.leida.is_(True), 1), else_=0)).label("leidas"),
        )
        .group_by(Notificacion.remitente_id, Notificacion.mensaje, Notificacion.created_at)
        .order_by(Notificacion.created_at.desc())
        .limit(limite)
        .all()
    )


def listar_por_destinatario(db: Session, destinatario_id: uuid.UUID) -> list[Notificacion]:
    return (
        db.query(Notificacion)
        .filter(Notificacion.destinatario_id == destinatario_id)
        .order_by(Notificacion.created_at.desc())
        .all()
    )


def marcar_leida(db: Session, notificacion_id: int, destinatario_id: uuid.UUID) -> Notificacion | None:
    """Solo el destinatario puede marcar su propia notificación como leída."""
    notificacion = (
        db.query(Notificacion)
        .filter(Notificacion.id == notificacion_id, Notificacion.destinatario_id == destinatario_id)
        .first()
    )
    if notificacion is None:
        return None
    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)
    return notificacion
