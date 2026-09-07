import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.sesion import Sesion


def crear(db: Session, usuario_id: uuid.UUID, ip: str | None) -> Sesion:
    sesion = Sesion(usuario_id=usuario_id, ip=ip)
    db.add(sesion)
    db.commit()
    db.refresh(sesion)
    return sesion


def abierta(db: Session, usuario_id: uuid.UUID) -> Sesion | None:
    """La sesión sin cerrar más reciente del usuario, si existe."""
    return (
        db.query(Sesion)
        .filter(Sesion.usuario_id == usuario_id, Sesion.fin.is_(None))
        .order_by(Sesion.inicio.desc())
        .first()
    )


def tocar(db: Session, usuario_id: uuid.UUID) -> Sesion | None:
    """El latido: refresca `ultima_actividad` de la sesión abierta."""
    sesion = abierta(db, usuario_id)
    if sesion is not None:
        sesion.ultima_actividad = datetime.now(timezone.utc)
        db.commit()
    return sesion


def cerrar(db: Session, usuario_id: uuid.UUID) -> Sesion | None:
    """Cierra la sesión abierta (logout)."""
    sesion = abierta(db, usuario_id)
    if sesion is not None:
        ahora = datetime.now(timezone.utc)
        sesion.fin = ahora
        sesion.ultima_actividad = ahora
        db.commit()
    return sesion


def listar(db: Session) -> list[Sesion]:
    """Todas las sesiones, la más reciente primero."""
    return db.query(Sesion).order_by(Sesion.inicio.desc()).all()
