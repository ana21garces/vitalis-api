from datetime import datetime

from pydantic import BaseModel


class InsigniaEstado(BaseModel):
    id: str
    nombre: str
    descripcion: str
    criterio: str
    icono: str
    rareza: str
    xp: int
    ganada: bool
    otorgada_at: datetime | None = None
    nueva: bool = False  # se ganó justo en esta consulta


class InsigniasResponse(BaseModel):
    total: int
    ganadas: int
    insignias: list[InsigniaEstado]
