import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Sesion(Base):
    """Una sesión de un usuario en la plataforma, para la auditoría de accesos.

    `inicio` se marca en el login y `fin` en el logout. `ultima_actividad` la
    refresca un «latido» periódico mientras la pestaña está abierta: así el
    tiempo de actividad es fiel aunque la persona cierre la pestaña sin dar
    logout (en ese caso la sesión queda sin `fin`, pero con la última señal).
    """

    __tablename__ = "sesiones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ip = Column(String(64), nullable=True)
    inicio = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ultima_actividad = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    fin = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Sesion id={self.id} usuario_id={self.usuario_id}>"
