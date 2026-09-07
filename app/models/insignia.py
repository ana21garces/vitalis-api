"""Insignias (medallas por hitos) que gana el estudiante.

Complementa la gamificación de Duvan (XP, niveles, rangos, rachas): esa premia
acumulación; esto premia hitos concretos. Solo guarda las que YA se ganaron;
qué insignias existen y cómo se ganan vive en `app/data/insignias_catalogo.py`.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class InsigniaUsuario(Base):
    __tablename__ = "insignias_usuario"
    __table_args__ = (
        UniqueConstraint("user_id", "insignia_id", name="uq_insignia_usuario"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    insignia_id = Column(String(40), nullable=False)  # id del catálogo, ej. "primer_paso"
    otorgada_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # NULL = automática. Cuando el "sello del profesional" exista, aquí va su id.
    otorgada_por = Column(UUID(as_uuid=True), nullable=True)
