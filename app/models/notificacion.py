import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Notificacion(Base):
    """Mensaje que un profesional envía a un estudiante desde su vista de
    resultados. Hoy solo existe un caso de uso —invitar a agendar una cita—
    pero el modelo no lo asume: es texto libre, no una plantilla fija."""

    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remitente_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    destinatario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mensaje = Column(Text, nullable=False)
    leida = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Notificacion id={self.id} destinatario_id={self.destinatario_id}>"
