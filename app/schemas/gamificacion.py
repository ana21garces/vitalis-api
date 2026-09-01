from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class ProgresoGamificacion(BaseModel):
    total_xp: int
    current_level: int
    rank_tier: str
    streak_days: int
    xp_en_nivel: int
    xp_para_siguiente: int
    avatar_url: str | None = None


class MisionResponse(BaseModel):
    id: UUID
    tarea_id: str
    dimension: str
    dimension_label: str
    titulo: str
    descripcion: str
    xp: int
    duracion_min: int | None
    completada: bool
    completada_at: datetime | None = None


class MisionesHoyResponse(BaseModel):
    fecha: date
    misiones: list[MisionResponse]
    completadas_hoy: int
    total_hoy: int
    bonus_disponible: int
    progreso: ProgresoGamificacion


class CompletarMisionResponse(BaseModel):
    mision: MisionResponse
    xp_ganado: int
    bonus_dia: int
    subio_nivel: bool
    nuevo_rank: str | None = None
    progreso: ProgresoGamificacion


class XpEventoResponse(BaseModel):
    id: UUID
    xp: int
    motivo: str
    referencia_id: str | None
    # Qué evento/actividad concreta dio los puntos (ej. "Caminata activa"),
    # resuelto desde referencia_id. None si no se pudo identificar.
    detalle: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
