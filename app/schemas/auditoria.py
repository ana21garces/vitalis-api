from datetime import datetime

from pydantic import BaseModel


class AuditoriaItem(BaseModel):
    usuario: str
    email: str
    tipo: str  # Usuario | Profesional
    evento: str  # login | logout
    ip: str | None
    fecha: datetime


class AuditoriaResponse(BaseModel):
    total: int
    items: list[AuditoriaItem]


class AuditoriaResumen(BaseModel):
    logins_hoy: int
    logouts_hoy: int
    activos_hoy: int
    duracion_promedio_min: float
