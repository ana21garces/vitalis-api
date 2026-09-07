from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.encuesta_hplp import TarjetaRecomendacion


class SeguimientoResponse(BaseModel):
    id: UUID
    dimension: str
    pregunta_num: int
    nivel: str
    estado: str
    racha_actual: int
    mejor_racha: int
    total_dias_registrados: int
    ultima_fecha_registro: date | None
    completada_at: datetime | None

    model_config = {"from_attributes": True}


class TarjetaConSeguimiento(BaseModel):
    tarjeta: TarjetaRecomendacion
    seguimiento: SeguimientoResponse


class TarjetasSeguimientoResponse(BaseModel):
    dimension: str
    nivel_dimension: str
    indice_dimension: float
    total: int
    tarjetas: list[TarjetaConSeguimiento]


class RegistrarDiaRequest(BaseModel):
    notas: str | None = Field(None, max_length=2000)


class RegistroDiarioResponse(BaseModel):
    id: UUID
    fecha: date
    notas: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RegistrarDiaResponse(BaseModel):
    seguimiento: SeguimientoResponse
    registro: RegistroDiarioResponse
    racha_aumento: bool


class ProgresoDimension(BaseModel):
    dimension: str
    dimension_label: str
    total: int
    activas: int
    completadas: int
    registradas_hoy: int = 0
    mensaje_cierre: str | None


class ProgresoSeguimientoResponse(BaseModel):
    dimensiones: list[ProgresoDimension]
