from sqlalchemy import Column, Date, DateTime, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class AsistenteSaludo(Base):
    __tablename__ = "asistente_saludos"
    __table_args__ = (UniqueConstraint("user_id", "fecha", name="uq_asistente_saludo_dia"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    mensaje = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
