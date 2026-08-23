"""Seguimiento diario del estudiante sobre las recomendaciones profesionales
(técnica/objetivo/instrucciones) generadas por `app/services/recomendaciones_*_service.py`.

Dos tablas, mismo patrón que `MisionDiaria`/`XpEvento` (app/models/gamificacion.py):
el padre acumula el estado y los contadores de racha, el hijo guarda un
registro por día (con notas opcionales) para poder consultar el historial.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class SeguimientoRecomendacion(Base):
    __tablename__ = "seguimientos_recomendacion"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "dimension", "pregunta_num", "nivel",
            name="uq_seguimiento_usuario_dim_pregunta_nivel",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    dimension = Column(String(50), nullable=False)
    pregunta_num = Column(Integer, nullable=False)
    nivel = Column(String(20), nullable=False)
    estado = Column(String(20), nullable=False, default="en_progreso")
    racha_actual = Column(Integer, nullable=False, default=0)
    mejor_racha = Column(Integer, nullable=False, default=0)
    total_dias_registrados = Column(Integer, nullable=False, default=0)
    ultima_fecha_registro = Column(Date, nullable=True)
    completada_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class RegistroDiarioSeguimiento(Base):
    __tablename__ = "registros_diarios_seguimiento"
    __table_args__ = (
        UniqueConstraint("seguimiento_id", "fecha", name="uq_registro_seguimiento_fecha"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seguimiento_id = Column(
        UUID(as_uuid=True), ForeignKey("seguimientos_recomendacion.id"), nullable=False, index=True,
    )
    fecha = Column(Date, nullable=False)
    notas = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
