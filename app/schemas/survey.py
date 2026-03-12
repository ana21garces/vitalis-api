from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict


class SurveySubmit(BaseModel):
    sexo: str
    ano_cursado: str
    answers: Dict[int, int]  # {1: 3, 2: 4, ...} pregunta: respuesta
    score_nutricion: float
    score_ejercicio: float
    score_responsabilidad_salud: float
    score_manejo_estres: float
    score_soporte_interpersonal: float
    score_autoactualizacion: float
    score_total: float


class SurveyResponse(BaseModel):
    id: UUID
    user_id: UUID
    sexo: str
    ano_cursado: str
    score_nutricion: float
    score_ejercicio: float
    score_responsabilidad_salud: float
    score_manejo_estres: float
    score_soporte_interpersonal: float
    score_autoactualizacion: float
    score_total: float
    completed_at: datetime

    model_config = {"from_attributes": True}