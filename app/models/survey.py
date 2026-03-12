import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Datos demográficos
    sexo = Column(String(20), nullable=False)
    ano_cursado = Column(String(20), nullable=False)
    
    # Las 48 respuestas en JSON {1: 3, 2: 1, ...}
    answers = Column(JSONB, nullable=False)
    
    # Puntajes por subescala
    score_nutricion = Column(Float, nullable=False)
    score_ejercicio = Column(Float, nullable=False)
    score_responsabilidad_salud = Column(Float, nullable=False)
    score_manejo_estres = Column(Float, nullable=False)
    score_soporte_interpersonal = Column(Float, nullable=False)
    score_autoactualizacion = Column(Float, nullable=False)
    score_total = Column(Float, nullable=False)
    
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="survey_responses")