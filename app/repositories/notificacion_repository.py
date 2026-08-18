import uuid
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
