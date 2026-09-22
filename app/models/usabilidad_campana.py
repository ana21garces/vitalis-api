from sqlalchemy import Boolean, Column, Date, DateTime, Integer, func

from app.db.base import Base


class UsabilidadCampana(Base):
    """Una sola fila (id=1) con el estado de la campaña de la encuesta de
    usabilidad: si está activa y en qué rango de fechas opcional se abre."""

    __tablename__ = "usabilidad_campana"

    id = Column(Integer, primary_key=True)
    activa = Column(Boolean, nullable=False, default=False)
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
