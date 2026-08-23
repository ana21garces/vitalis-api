import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class MisionDiaria(Base):
    __tablename__ = "misiones_diarias"
    __table_args__ = (
        UniqueConstraint("user_id", "fecha", "tarea_id", name="uq_mision_usuario_fecha_tarea"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    tarea_id = Column(String(10), nullable=False)
    dimension = Column(String(50), nullable=False)
    xp_otorgado = Column(Integer, nullable=False)
    completada_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class XpEvento(Base):
    __tablename__ = "xp_eventos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    xp = Column(Integer, nullable=False)
    motivo = Column(String(50), nullable=False)
    referencia_id = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
