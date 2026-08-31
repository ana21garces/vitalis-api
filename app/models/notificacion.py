import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Notificacion(Base):
    """Mensaje que aparece en la campana. Puede ir dirigido a una persona
    (destinatario_id) —invitar a un estudiante a agendar una cita, un anuncio—
    o a un rol (rol_destinatario) —una alerta de bienestar que ve el profesional
    de esa dimensión y también el administrador cuando entra a su vista—. Una de
    las dos direcciones va puesta, no las dos."""

    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remitente_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    destinatario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    # Rol al que va dirigida cuando no es para una persona puntual (las alertas).
    rol_destinatario = Column(String(50), nullable=True, index=True)
    # Rol desde el que se envía, para mostrar "Profesional de ..." en vez del
    # nombre de quien la mandó (p. ej. el admin actuando como ese profesional).
    remitente_rol = Column(String(50), nullable=True)
    mensaje = Column(Text, nullable=False)
    # Ruta interna a la que lleva la notificación al hacer clic (p. ej. la vista
    # del profesional con la persona resaltada). Null en las que son solo texto.
    enlace = Column(String(500), nullable=True)
    # Respuesta del estudiante a una invitación a cita: null | "aceptada" | "rechazada".
    respuesta = Column(String(20), nullable=True)
    # Clase de notificación, para estilizarla: null | "alerta" | "cita_aceptada".
    tipo = Column(String(30), nullable=True)
    leida = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Notificacion id={self.id} destinatario_id={self.destinatario_id}>"
