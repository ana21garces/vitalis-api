from datetime import date

from pydantic import BaseModel, field_validator, model_validator

from app.data.csuq import ESCALA_MAX, ESCALA_MIN, TOTAL_ITEMS


class UsabilidadCreate(BaseModel):
    respuestas: list[int]
    rol: str | None = None

    @field_validator("respuestas")
    @classmethod
    def validar_respuestas(cls, v: list[int]) -> list[int]:
        if len(v) != TOTAL_ITEMS:
            raise ValueError(f"Se esperan {TOTAL_ITEMS} respuestas")
        if any(r < ESCALA_MIN or r > ESCALA_MAX for r in v):
            raise ValueError(f"Cada respuesta debe estar entre {ESCALA_MIN} y {ESCALA_MAX}")
        return v


class UsabilidadEstado(BaseModel):
    respondida: bool
    requerida: bool
    abierta: bool


class UsabilidadResultado(BaseModel):
    sysuse: float
    infoqual: float
    interqual: float
    puntaje_global: float


class CampanaResponse(BaseModel):
    activa: bool
    fecha_inicio: date | None
    fecha_fin: date | None
    abierta: bool
    total_respuestas: int


class CampanaUpdate(BaseModel):
    activa: bool
    fecha_inicio: date | None = None
    fecha_fin: date | None = None

    @model_validator(mode="after")
    def validar_rango(self) -> "CampanaUpdate":
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha 'Hasta' no puede ser anterior a la fecha 'Desde'")
        return self
